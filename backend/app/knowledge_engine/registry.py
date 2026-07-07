"""
AFK Knowledge Engine — loader, validator, registry.

Implements KB_ARCHITECTURE.md (M3.3a scope): the Universal Knowledge Object
envelope, per-type schemas, filesystem discovery, relationship integrity,
and a read-only in-process registry.

Guarantees:
  * Deterministic: same files -> same registry, always.
  * Never-invent at build time: schema or relationship violations fail loudly.
  * Additive: nothing here touches the diagnostic code path. A parity test
    (tests/test_knowledge.py) proves the registry matches the engine's
    hard-coded knowledge until the engine migrates to consume it.
"""
import os
import re
from pathlib import Path

import yaml

KNOWLEDGE_DIR = Path(__file__).resolve().parents[3] / "knowledge"

# ---------------------------------------------------------------------------
# Universal Knowledge Object — the envelope every object must satisfy
# ---------------------------------------------------------------------------

ID_PATTERN = re.compile(r"^AFK-[A-Z]{3}-\d{4}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

VALIDATION_STATUSES = [
    "draft", "hypothesis", "literature_supported", "peer_reviewed",
    "observed", "validated", "canonical", "deprecated", "rejected", "archived",
]

# type name -> (id prefix, directory, extra required fields)
TYPE_REGISTRY = {
    "business_system":   ("SYS", "systems",           ["definition", "purpose"]),
    "constraint":        ("CON", "constraints",       ["definition", "affected_systems", "mechanism"]),
    "metric":            ("MET", "metrics",           ["definition", "unit", "computation", "direction"]),
    "treatment":         ("TRT", "treatments",        ["definition", "mechanism", "treats", "expected_outcome"]),
    "detection_rule":    ("DET", "detection_rules",   ["constraint_id", "logic", "evidence_map"]),
    "confidence_model":  ("CFM", "confidence_models", ["formula", "rationale"]),
    "priority_model":    ("PRI", "priority_models",    ["formula", "rationale", "factors"]),
    "questionnaire_item": ("QUE", "questionnaire",    ["text", "answer_type", "evidence_class"]),
    "evidence_rule":     ("EVR", "evidence_rules",    ["evidence_kind", "quality_criteria"]),
    "case_study":        ("CAS", "cases",             ["business_profile", "observation"]),
    "validation_protocol": ("VAL", "validation_protocols", ["protocol", "scorecard", "acceptance_criteria"]),
    "audit_spec":        ("AUD", "audit_specs",       ["spec_version", "question_reforms"]),
    "compound_pattern":  ("CMP", "compound_patterns", ["definition", "systems", "trigger"]),
    "moat_spec":         ("MOA", "moat_specs",        ["pillars", "competitive_frame"]),
}

RELATIONSHIP_TYPES = {
    "causes", "increases", "decreases", "creates_pressure_on",   # causal
    "part_of", "parent_of",                                      # structural
    "supports", "contradicts", "derived_from",                   # evidential
    "requires", "detects", "treats", "monitors", "informs",
    "measured_by", "contains",                                   # dependency
    "supersedes", "deprecated_by", "variant_of", "related_to",   # lineage
}

ENVELOPE_REQUIRED = ["id", "type", "name", "version", "status", "owner", "created", "description"]
ENVELOPE_OPTIONAL = ["changelog", "citations", "validation_records", "relationships",
                     "tags", "industries", "limitations", "notes", "supersedes",
                     "deprecated_by", "confidence", "todos"]


class KnowledgeError(Exception):
    """Raised when the knowledge base fails validation. Loud by design."""


def _validate_object(obj: dict, path: str) -> list[str]:
    errors = []
    for f in ENVELOPE_REQUIRED:
        if f not in obj or obj[f] in (None, ""):
            errors.append(f"{path}: missing required envelope field '{f}'")
    if errors:
        return errors

    if not ID_PATTERN.match(str(obj["id"])):
        errors.append(f"{path}: id '{obj['id']}' must match AFK-XXX-0000")
    if obj["type"] not in TYPE_REGISTRY:
        errors.append(f"{path}: unknown type '{obj['type']}'")
        return errors
    prefix, _dir, extra_required = TYPE_REGISTRY[obj["type"]]
    if not str(obj["id"]).startswith(f"AFK-{prefix}-"):
        errors.append(f"{path}: id prefix does not match type '{obj['type']}' (expected AFK-{prefix}-…)")
    if not VERSION_PATTERN.match(str(obj["version"])):
        errors.append(f"{path}: version '{obj['version']}' must be semver X.Y.Z")
    if obj["status"] not in VALIDATION_STATUSES:
        errors.append(f"{path}: status '{obj['status']}' not in validation ladder")
    for f in extra_required:
        if f not in obj or obj[f] in (None, "", []):
            errors.append(f"{path}: type '{obj['type']}' requires field '{f}'")
    created = obj.get("created") or {}
    for f in ("by", "date", "reason"):
        if f not in created:
            errors.append(f"{path}: created.{f} is required (provenance)")
    for rel in obj.get("relationships", []) or []:
        if rel.get("type") not in RELATIONSHIP_TYPES:
            errors.append(f"{path}: unknown relationship type '{rel.get('type')}'")
        if not rel.get("target"):
            errors.append(f"{path}: relationship missing target")
    return errors


class KnowledgeRegistry:
    """Read-only registry of every knowledge object, keyed by id, with a
    typed index and a relationship adjacency map. Built once, immutable."""

    def __init__(self, objects: dict[str, dict]):
        self._objects = objects
        self._by_type: dict[str, list[str]] = {}
        self._edges_out: dict[str, list[dict]] = {}
        self._edges_in: dict[str, list[dict]] = {}
        for oid, obj in objects.items():
            self._by_type.setdefault(obj["type"], []).append(oid)
            for rel in obj.get("relationships", []) or []:
                edge = {"source": oid, "type": rel["type"], "target": rel["target"],
                        "confidence": rel.get("confidence", "hypothesized")}
                self._edges_out.setdefault(oid, []).append(edge)
                self._edges_in.setdefault(rel["target"], []).append(edge)

    # -- lookups ------------------------------------------------------------
    def get(self, object_id: str) -> dict | None:
        return self._objects.get(object_id)

    def by_type(self, type_name: str) -> list[dict]:
        return [self._objects[i] for i in sorted(self._by_type.get(type_name, []))]

    def all_ids(self) -> list[str]:
        return sorted(self._objects.keys())

    def search(self, query: str, type_name: str | None = None,
               status: str | None = None) -> list[dict]:
        q = query.lower().strip()
        out = []
        for obj in self._objects.values():
            if type_name and obj["type"] != type_name:
                continue
            if status and obj["status"] != status:
                continue
            hay = " ".join([obj["name"], obj.get("description", ""),
                            " ".join(obj.get("tags", []) or [])]).lower()
            if q in hay or not q:
                out.append(obj)
        return sorted(out, key=lambda o: o["id"])

    def relationships(self, object_id: str) -> dict:
        return {"outgoing": self._edges_out.get(object_id, []),
                "incoming": self._edges_in.get(object_id, [])}

    def stats(self) -> dict:
        by_status: dict[str, int] = {}
        for o in self._objects.values():
            by_status[o["status"]] = by_status.get(o["status"], 0) + 1
        return {"total_objects": len(self._objects),
                "by_type": {t: len(ids) for t, ids in sorted(self._by_type.items())},
                "by_status": by_status,
                "total_relationships": sum(len(v) for v in self._edges_out.values()),
                "todos": sum(len(o.get("todos") or []) for o in self._objects.values())}


def load_registry(knowledge_dir: Path = KNOWLEDGE_DIR, strict: bool = True) -> KnowledgeRegistry:
    """Discover every .yaml under knowledge/, validate everything, check
    referential integrity, return the registry. Adding a new knowledge file
    requires zero code changes — this is the auto-discovery contract."""
    objects: dict[str, dict] = {}
    errors: list[str] = []

    for root, _dirs, files in os.walk(knowledge_dir):
        for fname in sorted(files):
            if not fname.endswith((".yaml", ".yml")):
                continue
            path = Path(root) / fname
            try:
                with open(path, "r", encoding="utf-8") as f:
                    obj = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"{path}: YAML parse error: {e}")
                continue
            if not isinstance(obj, dict):
                errors.append(f"{path}: not a mapping")
                continue
            errors.extend(_validate_object(obj, str(path.relative_to(knowledge_dir))))
            oid = obj.get("id")
            if oid in objects:
                errors.append(f"{path}: duplicate id {oid}")
            elif oid:
                obj["_source_file"] = str(path.relative_to(knowledge_dir))
                objects[oid] = obj

    # Referential integrity: every relationship target must exist
    for oid, obj in objects.items():
        for rel in obj.get("relationships", []) or []:
            if rel.get("target") not in objects:
                errors.append(f"{obj['_source_file']}: dangling relationship "
                              f"{oid} --{rel.get('type')}--> {rel.get('target')} (target not found)")

    if errors and strict:
        raise KnowledgeError("Knowledge base failed validation:\n  " + "\n  ".join(errors))
    return KnowledgeRegistry(objects)


# Singleton for the app (loaded lazily; a bad KB fails at first use, loudly)
_registry: KnowledgeRegistry | None = None


def get_registry() -> KnowledgeRegistry:
    global _registry
    if _registry is None:
        _registry = load_registry()
    return _registry

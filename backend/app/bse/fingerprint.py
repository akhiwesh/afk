"""Deterministic input fingerprint for provenance and reproducibility."""
import hashlib
import json
from typing import Any


def _canonicalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj)}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize(v) for v in obj]
    return obj


def input_fingerprint(audit_answers: dict, evidence_records: dict[str, list[dict]]) -> str:
    payload = {
        "audit": _canonicalize(audit_answers),
        "evidence": _canonicalize(evidence_records),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
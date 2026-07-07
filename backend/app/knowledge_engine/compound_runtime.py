"""Evaluate AFK-CMP-* compound patterns from KB with engine fallback."""
from __future__ import annotations

from functools import lru_cache

COMPOUND_PACK_ID = "kb-cmp-v1"

_FALLBACK_PATTERNS: list[dict] = [
    {
        "id": "AFK-CMP-0001",
        "systems": ["demand", "conversion"],
        "definition": "Funnel is too thin to diagnose conversion precisely — fix lead volume before optimizing close mechanics.",
        "trigger": {
            "all_weak": [{"system": "demand", "threshold": 70}, {"system": "conversion", "threshold": 70}],
            "conditions": [{"field": "leads_per_month", "compare": "lt", "value": 20}],
        },
    },
    {
        "id": "AFK-CMP-0002",
        "systems": ["qualification", "conversion"],
        "definition": "This may be a lead-quality problem disguised as a sales problem — calendar pollution upstream inflates close-rate pain.",
        "trigger": {
            "all_weak": [{"system": "qualification", "threshold": 70}, {"system": "conversion", "threshold": 70}],
        },
    },
    {
        "id": "AFK-CMP-0003",
        "systems": ["pricing"],
        "definition": "Double monetization leak — underpriced positioning plus routine discounting compounds margin erosion.",
        "trigger": {
            "all_weak": [{"system": "pricing", "threshold": 80}],
            "conditions": [{
                "compare": "all_eq",
                "pairs": {"pricing_confidence": "Probably underpriced", "discounting": "Sometimes"},
            }],
        },
    },
]


@lru_cache(maxsize=1)
def _registry():
    from backend.app.knowledge_engine.registry import load_registry
    return load_registry()


def compound_pattern_catalog() -> list[dict]:
    """KB compound patterns sorted by id; falls back to engine defaults."""
    try:
        patterns = _registry().by_type("compound_pattern")
        if patterns:
            return sorted(patterns, key=lambda p: p["id"])
    except Exception:
        pass
    return list(_FALLBACK_PATTERNS)


def _num(answers: dict, field: str) -> float | None:
    raw = answers.get(field)
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _eval_trigger(trigger: dict, answers: dict, by_key: dict[str, dict]) -> bool:
    for weak in trigger.get("all_weak", []):
        dim = by_key.get(weak["system"])
        threshold = weak.get("threshold", 70)
        if dim is None or dim.get("score") is None or dim["score"] >= threshold:
            return False
    for cond in trigger.get("conditions", []):
        compare = cond.get("compare")
        if compare == "lt":
            num = _num(answers, cond["field"])
            if num is None or num >= cond["value"]:
                return False
        elif compare == "all_eq":
            for field, expected in (cond.get("pairs") or {}).items():
                if answers.get(field) != expected:
                    return False
    return True


def evaluate_compound_findings(answers: dict, dims: list[dict]) -> list[dict]:
    """Return fired compound findings with compound_id, systems, reasoning."""
    by_key = {d["key"]: d for d in dims if d.get("score") is not None}
    out: list[dict] = []
    for pattern in compound_pattern_catalog():
        if not _eval_trigger(pattern.get("trigger") or {}, answers, by_key):
            continue
        out.append({
            "compound_id": pattern["id"],
            "systems": pattern.get("systems") or [],
            "reasoning": pattern.get("definition") or pattern.get("name", ""),
        })
    return out


def clear_cache():
    _registry.cache_clear()
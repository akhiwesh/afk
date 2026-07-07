"""Load operational constants from Knowledge Base at runtime — deterministic fallback to engine defaults."""
from functools import lru_cache

from backend.app.knowledge_engine.registry import load_registry


@lru_cache(maxsize=1)
def _registry():
    return load_registry()


def priority_adjunct_config() -> dict:
    """AFK-PRI-0001 evidence adjunct thresholds. Falls back if KB unavailable."""
    defaults = {
        "pricing_discount_threshold_pct": 5.0,
        "pricing_discount_slope": 2.0,
        "pricing_discount_cap": 2.0,
        "retention_repeat_gap_pp": 20.0,
        "retention_repeat_slope": 3.0,
        "retention_repeat_cap": 1.75,
    }
    try:
        pri = _registry().get("AFK-PRI-0001")
        adjunct = (pri or {}).get("evidence_adjunct", {})
        disc = adjunct.get("pricing_discount_exposure", {})
        ret = adjunct.get("retention_repeat_exposure", {})
        if disc.get("threshold_pct") is not None:
            defaults["pricing_discount_threshold_pct"] = float(disc["threshold_pct"])
        if disc.get("slope") is not None:
            defaults["pricing_discount_slope"] = float(disc["slope"])
        if disc.get("cap") is not None:
            defaults["pricing_discount_cap"] = float(disc["cap"])
        if ret.get("gap_pp") is not None:
            defaults["retention_repeat_gap_pp"] = float(ret["gap_pp"])
        if ret.get("slope") is not None:
            defaults["retention_repeat_slope"] = float(ret["slope"])
        if ret.get("cap") is not None:
            defaults["retention_repeat_cap"] = float(ret["cap"])
        defaults["kb_object"] = pri.get("id") if pri else None
        defaults["kb_version"] = pri.get("version") if pri else None
    except Exception:
        defaults["kb_object"] = None
    return defaults


def clear_cache():
    _registry.cache_clear()
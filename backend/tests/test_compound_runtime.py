from backend.app.core import engine as ce
from backend.app.knowledge_engine.compound_runtime import (
    COMPOUND_PACK_ID,
    compound_pattern_catalog,
    evaluate_compound_findings,
    _FALLBACK_PATTERNS,
)
from backend.app.knowledge_engine.registry import load_registry
from backend.tests.test_engine import FULL_ANSWERS


def test_compound_catalog_loads_from_kb():
    catalog = compound_pattern_catalog()
    assert len(catalog) == 3
    assert catalog[0]["id"].startswith("AFK-CMP-")


def test_full_answers_fire_expected_compound_patterns():
    h = ce.compute_health(FULL_ANSWERS)
    ids = {c["compound_id"] for c in h.get("compound_findings", [])}
    assert "AFK-CMP-0001" in ids
    assert "AFK-CMP-0003" in ids


def test_compound_parity_kb_matches_fallback_catalog():
    r = load_registry()
    kb = {o["id"]: o for o in r.by_type("compound_pattern")}
    assert len(kb) == len(_FALLBACK_PATTERNS)
    for fb in _FALLBACK_PATTERNS:
        obj = kb[fb["id"]]
        assert obj["definition"] == fb["definition"]
        assert obj["systems"] == fb["systems"]
        assert obj["trigger"] == fb["trigger"]


def test_evaluate_compound_findings_shape():
    h = ce.compute_health(FULL_ANSWERS)
    fired = evaluate_compound_findings(FULL_ANSWERS, h["dimensions"])
    assert fired
    for f in fired:
        assert f["compound_id"].startswith("AFK-CMP-")
        assert f["systems"]
        assert f["reasoning"]


def test_science_provenance_includes_compound_pack():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["science_provenance"]["compound_pack"] == COMPOUND_PACK_ID
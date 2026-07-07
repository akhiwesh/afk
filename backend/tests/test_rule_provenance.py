from backend.app.core import engine as ce


def test_full_answers_findings_carry_rule_ids():
    from backend.tests.test_engine import FULL_ANSWERS
    h = ce.compute_health(FULL_ANSWERS)
    ruled = [
        f for d in h["dimensions"] for f in d["findings"] if f.get("rule_id")
    ]
    assert len(ruled) >= 5
    assert all(f.get("rule_pack") == "kb-det-v1" for f in ruled)
    assert any(f["rule_id"] == "AFK-DET-0007" for f in ruled)


def test_optional_questions_not_in_dimension_scoring():
    assert "gross_margin_band" in ce.QUESTION_IDS
    assert "gross_margin_band" not in {
        f for meta in ce.DIMENSIONS.values() for f in meta["fields"]
    }


def test_det_parity_findings_map_to_registry():
    from backend.tests.test_engine import FULL_ANSWERS
    from backend.app.knowledge_engine.registry import load_registry
    from backend.app.knowledge_engine.rule_provenance import mapped_rule_ids

    registry_det = {o["id"] for o in load_registry().by_type("detection_rule")}
    for rid in mapped_rule_ids():
        assert rid in registry_det, f"{rid} missing from KB registry"

    h = ce.compute_health(FULL_ANSWERS)
    emitted = {
        f["rule_id"]
        for d in h["dimensions"]
        for f in d["findings"]
        if f.get("rule_id")
    }
    assert emitted <= registry_det
    assert len(emitted) >= 5


def test_det_penalty_parity_exact_map_matches_registry():
    from backend.app.knowledge_engine.registry import load_registry
    from backend.app.knowledge_engine.rule_provenance import exact_map_penalties

    r = load_registry()
    for rid, penalty in exact_map_penalties().items():
        det = r.get(rid)
        assert det is not None, f"{rid} missing"
        assert det["penalty"] == penalty, f"{rid}: engine map {penalty} != KB {det['penalty']}"
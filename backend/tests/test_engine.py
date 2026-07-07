"""Constraint Engine V1 — the engine must never guess, and every
conclusion must carry evidence, reasoning, and confidence."""
from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi


FULL_ANSWERS = {
    "business_type": "B2B services / agency", "industry": "Consulting", "team_size": 6,
    "growth_stage": "Early revenue (finding repeatability)",
    "monthly_revenue": 850000, "revenue_model": "Mixed", "avg_deal_value": 150000,
    "revenue_goal_12m": 2500000,
    "leads_per_month": 14, "lead_sources_count": "One",
    "primary_lead_source": "Referrals / word of mouth", "marketing_active": "Sporadic",
    "qualification_process": "Informal gut-feel", "pct_leads_worth_it": 40,
    "conversion_close_rate": 22, "conversion_followups": "2",
    "conversion_owner": "Founder leads most deals",
    "conversion_process": "Mostly in people's heads", "conversion_cycle_days": 35,
    "pricing_confidence": "Probably underpriced", "last_price_change": "Never",
    "discounting": "Sometimes",
    "repeat_rate": 45, "churn_reason_known": "Partially / anecdotally", "retention_process": "Ad-hoc",
    "founder_in_every_sale": "Yes, every deal", "documented_sales_process": "No",
    "self_diagnosis": "Need more leads", "biggest_worry": "Churn",
}

# Founder believes things are fine — Phase 1 must not score 98 "Low Risk"
SOFT_ANSWERS = {
    "business_type": "B2B services / agency", "industry": "Consulting", "team_size": 6,
    "growth_stage": "Growing (repeatable sales)",
    "monthly_revenue": 850000, "revenue_model": "Mixed", "avg_deal_value": 150000,
    "revenue_goal_12m": 2500000,
    "leads_per_month": 50, "lead_sources_count": "Two or three",
    "primary_lead_source": "Referrals / word of mouth", "marketing_active": "Yes, systematic",
    "qualification_process": "Documented criteria the team follows", "pct_leads_worth_it": 55,
    "conversion_close_rate": 35, "conversion_followups": "3",
    "conversion_owner": "Mostly team",
    "conversion_process": "Partially documented", "conversion_cycle_days": 45,
    "pricing_confidence": "About right", "last_price_change": "More than a year ago",
    "discounting": "Sometimes",
    "repeat_rate": 50, "churn_reason_known": "Partially / anecdotally", "retention_process": "Ad-hoc",
    "founder_in_every_sale": "Most deals", "documented_sales_process": "Yes",
    "self_diagnosis": "Scaling the team", "biggest_worry": "Hiring",
}


def test_empty_answers_yield_insufficient_never_a_guess():
    h = ce.compute_health({})
    assert h["sufficient"] is False
    assert "health_score" not in h
    assert "Not enough evidence" in h["message"]


def test_full_audit_produces_scored_diagnosis():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["sufficient"] is True
    assert 0 <= h["health_score"] <= 100
    assert h["risk_level"] in ("Low Risk", "Moderate Risk", "High Risk")
    assert 0 < h["confidence"] <= 1
    assert h["primary_constraint"]["label"]
    assert h["recommended_next_step"]


def test_every_finding_carries_evidence_and_reasoning():
    h = ce.compute_health(FULL_ANSWERS)
    for dim in h["dimensions"]:
        for f in dim["findings"]:
            assert f["reasoning"], f"finding without reasoning in {dim['key']}"
            assert f["evidence"], f"finding without evidence in {dim['key']}"
            for e in f["evidence"]:
                # evidence must cite a real answered question
                assert e["id"] in FULL_ANSWERS


def test_opportunity_only_exists_with_revenue_evidence():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["revenue_opportunity"] is not None
    assert "Directional range" in h["revenue_opportunity"]["basis"]
    assert h["revenue_opportunity"]["amount_low"] < h["revenue_opportunity"]["amount_high"]

    no_rev = {k: v for k, v in FULL_ANSWERS.items() if k != "monthly_revenue"}
    h2 = ce.compute_health(no_rev)
    assert h2["revenue_opportunity"] is None  # no revenue stated -> no ₹ claim


def test_partial_dimension_gets_no_score():
    # Answer only 2 of 5 conversion fields -> confidence 0.4 -> unscored (Phase 1: requires 100%)
    partial = dict(FULL_ANSWERS)
    for k in ("conversion_close_rate", "conversion_followups", "conversion_owner"):
        partial.pop(k)
    h = ce.compute_health(partial)
    conv = next(d for d in h["dimensions"] if d["key"] == "conversion")
    assert not ce._dimension_scorable(conv["coverage"])
    assert conv["score"] is None
    assert conv["missing"]


def test_twin_reflects_answers_verbatim_not_ai():
    t = ce.compute_twin(FULL_ANSWERS)
    assert t["profile"]["business_type"] == FULL_ANSWERS["business_type"]
    assert t["profile"]["monthly_revenue"] == FULL_ANSWERS["monthly_revenue"]
    assert t["self_diagnosis"] == FULL_ANSWERS["self_diagnosis"]
    assert t["completeness"] == 1.0
    assert isinstance(t["constraints"], list)


def test_founder_dependency_detected():
    h = ce.compute_health(FULL_ANSWERS)
    fd = next(d for d in h["dimensions"] if d["key"] == "founder_dependency")
    assert fd["score"] is not None and fd["score"] < 100
    texts = " ".join(f["reasoning"] for f in fd["findings"])
    assert "founder" in texts.lower() or "delegate" in texts.lower()


# ---------------------------------------------------------------------------
# M2.1 — Founder experience layer
# ---------------------------------------------------------------------------

def test_dna_derives_only_from_evidence():
    dna = ce.compute_dna(FULL_ANSWERS)
    by_label = {t["label"]: t for t in dna}
    assert by_label["Growth Style"]["value"] == "Founder-led"
    assert by_label["Revenue Engine"]["value"] == "Referral-driven"
    # Every known trait must cite its source question
    for t in dna:
        if t["known"]:
            assert t["source"]
    # No evidence -> says so, never guesses
    empty = ce.compute_dna({})
    assert all("not enough evidence" in t["value"] for t in empty)


def test_narrative_is_deterministic_and_grounded():
    n1 = ce.compute_narrative(FULL_ANSWERS, "Acme")
    n2 = ce.compute_narrative(FULL_ANSWERS, "Acme")
    assert n1 == n2  # deterministic
    assert n1.startswith("Acme is a founder-led")
    assert ce.compute_narrative({}) is None  # insufficient -> no story


def test_open_questions_prefer_real_gaps():
    partial = dict(FULL_ANSWERS)
    partial.pop("conversion_close_rate")
    qs = ce.compute_open_questions(partial)
    assert qs and len(qs) <= 5
    assert any("paying customers" in q for q in qs)  # the actual missing field


def test_open_questions_prompt_on_unknown_margin():
    answers = dict(FULL_ANSWERS)
    answers["gross_margin_band"] = "Unknown"
    qs = ce.compute_open_questions(answers)
    assert any("gross margin" in q.lower() for q in qs)


def test_open_questions_prompt_on_unknown_cac():
    answers = dict(FULL_ANSWERS)
    answers["cac_known"] = "No"
    qs = ce.compute_open_questions(answers)
    assert any("cac" in q.lower() or "marketing and sales" in q.lower() for q in qs)


def test_compound_findings_carry_compound_ids():
    h = ce.compute_health(FULL_ANSWERS)
    compound = h.get("compound_findings") or []
    ids = {c["compound_id"] for c in compound if c.get("compound_id")}
    assert ids <= {"AFK-CMP-0001", "AFK-CMP-0002", "AFK-CMP-0003"}


def test_conversion_v2_spec_example_scores_47_critical():
    answers = {
        "conversion_close_rate": 32,
        "conversion_followups": "2",
        "conversion_owner": "Founder leads most deals",
        "conversion_process": "Mostly in people's heads",
        "conversion_cycle_days": 55,
    }
    score = ce._conversion_score(answers)
    assert score == 47
    assert ce.conversion_status(score) == "Critical"
    finding = ce.build_conversion_system_finding(answers)
    assert finding["score"] == 47
    assert finding["status"] == "Critical"
    assert "Score: 47/100 (Critical)" in finding["formatted"]
    for key in ("finding", "root_cause", "business_impact", "recommended_action", "expected_outcome"):
        assert finding[key]


def test_evidence_stats_are_real_counts():
    st = ce.evidence_stats(FULL_ANSWERS)
    assert st["audit_answers"] == len(FULL_ANSWERS)
    assert st["findings"] > 0
    assert st["evidence_citations"] >= st["findings"]
    assert st["total_points"] == st["audit_answers"] + st["evidence_citations"]


def test_recommendation_card_is_complete():
    r = ce.compute_recommendation(FULL_ANSWERS)
    for k in ("action", "why", "evidence", "confidence_pct", "assumptions", "expected_impact"):
        assert r.get(k) not in (None, "", []), f"missing {k}"
    assert ce.compute_recommendation({}) is None


# ---------------------------------------------------------------------------
# Phase 1 — Honesty patch (DIAGNOSTIC_REDESIGN_V3.md)
# ---------------------------------------------------------------------------

def test_phase1_troubled_profile_health_at_most_55():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["sufficient"]
    assert h["health_score"] <= 55
    assert h["risk_level"] == "High Risk"
    assert h["primary_constraint"]["key"] in ("conversion", "pricing", "qualification", "founder_dependency")


def test_phase1_troubled_profile_no_silent_100s():
    h = ce.compute_health(FULL_ANSWERS)
    scored = [d for d in h["dimensions"] if d["score"] is not None]
    assert not any(d["score"] == 100 for d in scored), "troubled profile must not show Healthy 100s"


def test_phase1_soft_profile_not_false_negative():
    h = ce.compute_health(SOFT_ANSWERS)
    assert h["sufficient"]
    assert h["health_score"] <= 70
    watch_plus = sum(1 for d in h["dimensions"] if d["score"] is not None and d["score"] <= 75)
    assert watch_plus >= 2


def test_phase1_all_systems_structured_finding():
    for dim_key in ce.DIMENSIONS:
        sf = ce.build_system_finding(dim_key, FULL_ANSWERS)
        for key in ("finding", "root_cause", "business_impact", "score_line", "recommended_action", "expected_outcome", "formatted"):
            assert sf.get(key), f"missing {key} on {dim_key}"


def test_phase1_chain_cap_and_compound_findings():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["weakest_system_score"] < 55
    assert h["health_score"] <= 55
    assert isinstance(h.get("compound_findings"), list)


def test_epistemic_confidence_capped_without_uploaded_evidence():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["confidence"] <= evi.QUESTIONNAIRE_CEILING + 0.05
    for d in h["dimensions"]:
        if d.get("coverage", 0) >= 1.0 and d["key"] != "founder_dependency":
            assert d["confidence"] <= evi.QUESTIONNAIRE_CEILING + 0.01


def test_funnel_coherence_flags_arithmetic_gap():
    h = ce.compute_health(FULL_ANSWERS)
    fc = h.get("funnel_coherence")
    assert fc and fc["verdict"] == "incoherent"
    assert fc["stated_monthly_revenue"] > fc["theoretical_monthly_revenue"]


def test_hypothesis_verdict_contradicts_wrong_belief():
    h = ce.compute_health(FULL_ANSWERS)
    hv = h.get("hypothesis_verdict")
    assert hv["verdict"] == "contradicted"
    assert hv["inferred_belief_system"] == "demand"
    assert h["primary_constraint"]["key"] != "demand"


# ---------------------------------------------------------------------------
# Research Loop #2 — Impact priority + epistemic productization
# ---------------------------------------------------------------------------

def test_compute_constraint_priority_is_deterministic():
    p1 = ce.compute_constraint_priority("conversion", 25)
    p2 = ce.compute_constraint_priority("conversion", 25)
    assert p1 == p2
    assert p1["priority_score"] > ce.compute_constraint_priority("qualification", 65)["priority_score"]


def test_impact_priority_overrides_lowest_score():
    scored = [
        {"key": "demand", "label": "Lead Volume & Demand", "score": 30, "confidence": 0.4, "findings": []},
        {"key": "qualification", "label": "Lead Qualification", "score": 28, "confidence": 0.4, "findings": []},
    ]
    primary, lowest, ranking = ce._select_primary_constraint(scored)
    assert lowest["key"] == "qualification"
    assert primary["key"] == "demand"
    assert ranking[0]["key"] == "demand"


def test_full_answers_impact_priority_metadata():
    h = ce.compute_health(FULL_ANSWERS)
    pc = h["primary_constraint"]
    assert pc["key"] == "conversion"
    assert pc["selection_method"] == "impact_priority"
    assert pc["priority"]["priority_score"] > 0
    assert pc["priority"]["model_id"] == ce.PRIORITY_MODEL_ID
    assert isinstance(h["constraint_priority_ranking"], list)
    assert h["constraint_priority_ranking"][0]["key"] == pc["key"]
    assert ce.PRIORITY_MODEL_ID in h["method_note"]


def test_evidence_repeat_gap_boosts_retention_priority():
    scores = [
        {"key": "retention", "label": "Retention & Repeat Revenue", "score": 70, "confidence": 0.7, "findings": []},
        {"key": "conversion", "label": "Sales Conversion & Follow-up", "score": 65, "confidence": 0.7, "findings": []},
    ]
    answers = {"repeat_rate": 62}
    metrics = {"repeat_customer_rate": {"value": 100, "basis": "test"}}
    adj = ce.compute_evidence_priority_adjustments(metrics, answers)
    assert "retention" in adj
    primary, _, _ = ce._select_primary_constraint(scores, adj)
    assert primary["key"] == "retention"


def test_science_provenance_on_diagnosis():
    h = ce.compute_health(FULL_ANSWERS)
    sp = h.get("science_provenance")
    assert sp["priority_model_id"] == ce.PRIORITY_MODEL_ID
    assert sp["validation_protocol_id"] == "AFK-VAL-0001"


def test_evidence_discount_boosts_pricing_priority():
    scores = [
        {"key": "pricing", "label": "Pricing & Monetization", "score": 55, "confidence": 0.7, "findings": []},
        {"key": "conversion", "label": "Sales Conversion & Follow-up", "score": 65, "confidence": 0.7, "findings": []},
    ]
    base_primary, _, _ = ce._select_primary_constraint(scores)
    assert base_primary["key"] == "conversion"
    metrics = {"avg_discount_pct": {"value": 6.1, "basis": "test"}}
    adj = ce.compute_evidence_priority_adjustments(metrics)
    assert "pricing" in adj
    boosted_primary, _, _ = ce._select_primary_constraint(scores, adj)
    assert boosted_primary["key"] == "pricing"


def test_audit_wizard_diagnosis_preview_when_complete():
    from backend.app.core import audit_modules as am
    state = am.list_modules_state(FULL_ANSWERS)
    assert state["systems_complete"] == state["systems_total"]
    preview = state.get("diagnosis_preview")
    assert preview
    assert preview["primary_constraint"]
    assert preview["hypothesis_verdict"]["verdict"] == "contradicted"
    assert preview["priority_model"] == ce.PRIORITY_MODEL_ID

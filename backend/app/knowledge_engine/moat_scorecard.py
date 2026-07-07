"""Machine-verified competitive moat scorecard (AFK-MOA-0001)."""
from __future__ import annotations

from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi
from backend.app.knowledge_engine.registry import load_registry
from backend.app.knowledge_engine.rule_provenance import exact_map_penalties, mapped_rule_ids
from backend.app.knowledge_engine.validation_framework import score_corpus
MOAT_SPEC_ID = "AFK-MOA-0001"

# Canonical sufficient audit — mirrors test_engine.FULL_ANSWERS for deterministic moat checks
_CANONICAL_ANSWERS = {
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


def _check_epistemic_honesty() -> dict:
    r = load_registry()
    cfm = r.get("AFK-CFM-0001") or {}
    ceiling_ok = cfm.get("questionnaire_ceiling") == evi.QUESTIONNAIRE_CEILING
    h = ce.compute_health(_CANONICAL_ANSWERS)
    dims_have_conf = all("confidence" in d for d in h.get("dimensions", []))
    capped = any(d.get("confidence", 1) <= evi.QUESTIONNAIRE_CEILING + 0.01 for d in h.get("dimensions", []))
    passed = ceiling_ok and dims_have_conf and capped
    return {
        "pillar_id": "epistemic_honesty",
        "passed": passed,
        "evidence": {
            "kb_ceiling": cfm.get("questionnaire_ceiling"),
            "runtime_ceiling": evi.QUESTIONNAIRE_CEILING,
            "dimensions_with_confidence": dims_have_conf,
        },
    }


def _check_scientific_versioning() -> dict:
    h = ce.compute_health(_CANONICAL_ANSWERS)
    sp = h.get("science_provenance") or {}
    ruled = sum(
        1 for d in h.get("dimensions", []) for f in d.get("findings", []) if f.get("rule_id")
    )
    compounds = [c for c in h.get("compound_findings", []) if c.get("compound_id")]
    passed = (
        sp.get("rule_pack") == "kb-det-v1"
        and sp.get("compound_pack") == "kb-cmp-v1"
        and ruled >= 5
        and len(compounds) >= 1
    )
    return {
        "pillar_id": "scientific_versioning",
        "passed": passed,
        "evidence": {
            "rule_pack": sp.get("rule_pack"),
            "compound_pack": sp.get("compound_pack"),
            "ruled_findings": ruled,
            "compound_patterns": len(compounds),
        },
    }


def _check_kb_parity() -> dict:
    r = load_registry()
    stats = r.stats()
    ques = len(r.by_type("questionnaire_item"))
    compounds = len(r.by_type("compound_pattern"))
    dets = {o["id"] for o in r.by_type("detection_rule")}
    map_ok = mapped_rule_ids() <= dets
    pen_ok = all(
        (r.get(rid) or {}).get("penalty") == pen
        for rid, pen in exact_map_penalties().items()
    )
    passed = (
        ques == len(ce.QUESTIONS) + len(ce.OPTIONAL_QUESTIONS)
        and compounds == 3
        and map_ok
        and pen_ok
    )
    return {
        "pillar_id": "kb_parity",
        "passed": passed,
        "evidence": {
            "questionnaire_items": ques,
            "compound_patterns": compounds,
            "det_map_subset": map_ok,
            "penalty_parity": pen_ok,
            "total_objects": stats["total_objects"],
        },
    }


def _check_validation_discipline() -> dict:
    r = load_registry()
    val = r.get("AFK-VAL-0001")
    corpus = score_corpus()
    passed = (
        val is not None
        and corpus.get("protocol_id") == "AFK-VAL-0001"
        and corpus.get("calibration_ready") is False
        and corpus.get("cases_scored", 0) < 10
    )
    return {
        "pillar_id": "validation_discipline",
        "passed": passed,
        "evidence": {
            "cases_scored": corpus.get("cases_scored"),
            "calibration_ready": corpus.get("calibration_ready"),
            "corpus_mean_agreement": corpus.get("corpus_mean_agreement"),
        },
    }


def _check_deterministic_diagnosis() -> dict:
    a = ce.compute_health(_CANONICAL_ANSWERS)
    b = ce.compute_health(_CANONICAL_ANSWERS)
    passed = a.get("health_score") == b.get("health_score") and a.get("primary_constraint", {}).get("key") == b.get("primary_constraint", {}).get("key")
    return {
        "pillar_id": "deterministic_diagnosis",
        "passed": passed,
        "evidence": {"health_score": a.get("health_score"), "primary": a.get("primary_constraint", {}).get("key")},
    }


def _check_belief_evidence_split() -> dict:
    h = ce.compute_health(_CANONICAL_ANSWERS)
    hv = h.get("hypothesis_verdict")
    from backend.app.core import evidence_intel as evi_mod
    has_contra = callable(getattr(evi_mod, "detect_contradictions", None))
    passed = hv is not None and "verdict" in hv and has_contra
    return {
        "pillar_id": "belief_evidence_split",
        "passed": passed,
        "evidence": {"hypothesis_verdict": hv.get("verdict") if hv else None, "contradiction_detector": has_contra},
    }


def _check_never_invent_ladder() -> dict:
    r = load_registry()
    non_hypothesis = [oid for oid in r.all_ids() if r.get(oid)["status"] != "hypothesis"]
    passed = len(non_hypothesis) == 0
    return {
        "pillar_id": "never_invent_ladder",
        "passed": passed,
        "evidence": {"non_hypothesis_count": len(non_hypothesis), "total_objects": len(r.all_ids())},
    }


_PILLAR_CHECKS = [
    _check_epistemic_honesty,
    _check_scientific_versioning,
    _check_kb_parity,
    _check_validation_discipline,
    _check_deterministic_diagnosis,
    _check_belief_evidence_split,
    _check_never_invent_ladder,
]


def compute_moat_scorecard() -> dict:
    """Returns weighted moat score and per-pillar machine verification."""
    spec = load_registry().get(MOAT_SPEC_ID) or {}
    weights = {p["id"]: p.get("weight", 1) for p in spec.get("pillars", [])}
    total_weight = sum(weights.values()) or len(_PILLAR_CHECKS)

    results = [fn() for fn in _PILLAR_CHECKS]
    earned = sum(weights.get(r["pillar_id"], 1) for r in results if r["passed"])
    score = round(100 * earned / total_weight, 1)

    return {
        "moat_spec_id": MOAT_SPEC_ID,
        "competitive_frame": spec.get("competitive_frame", ""),
        "moat_score": score,
        "pillars_passed": sum(1 for r in results if r["passed"]),
        "pillars_total": len(results),
        "pillars": results,
        "aim": "Outperform generic AI business tools via auditable science, not fluent advice.",
        "honest_limit": "Score measures infrastructure readiness — not market share or NPS.",
    }
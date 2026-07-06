"""
CaseStudy builder — M3.5. Turns one organization's real state (audit +
evidence metrics + diagnosis) into an ANONYMIZED case study draft.

Privacy rules (hard, not configurable):
  * No organization name. No customer names. No emails, phones, filenames.
  * Revenue and team size are banded, never exact.
  * Industry passes through but is founder-editable at approval time.
  * The founder must explicitly approve before anything is written to the
    knowledge base. Drafts live only in the API response.
Cases enter the KB at status `observed` with synthetic=false — they ARE
observations, the raw material of the validation ladder.
"""
from backend.app.core import engine as ce


def _band(value, edges, labels, fallback):
    if not isinstance(value, (int, float)):
        return None
    for lim, lab in zip(edges, labels):
        if value < lim:
            return lab
    return fallback


def revenue_band(v):
    return _band(v, [200000, 500000, 1000000, 2500000, 10000000],
                 ["<2L", "2L-5L", "5L-10L", "10L-25L", "25L-1Cr"], "1Cr+")


def team_band(v):
    return _band(v, [4, 11, 26, 51], ["1-3", "4-10", "11-25", "26-50"], "50+")


_FORBIDDEN_METRIC_KEYS = {"top_lead_source"}  # categorical values could leak names


def build_case(answers: dict, health: dict, metrics: dict,
               contradictions: list, evidence_kinds: dict) -> dict:
    """Anonymized case draft. Everything identifying is banded or dropped."""
    safe_metrics = {}
    for k, m in (metrics or {}).items():
        if k in _FORBIDDEN_METRIC_KEYS:
            continue
        safe_metrics[k] = {"value": m["value"]}  # basis text can mention row counts; keep value only

    safe_contradictions = [
        {"belief_question": c["belief"]["question"],
         "belief_answer": str(c["belief"]["answer"]),
         "evidence_metric": c["evidence"]["metric"],
         "evidence_value": c["evidence"]["value"],
         "severity": c["severity"]}
        for c in (contradictions or [])
    ]

    diagnosis = None
    if health.get("sufficient"):
        diagnosis = {
            "health_score": health["health_score"],
            "risk_level": health["risk_level"],
            "confidence": health.get("confidence"),
            "primary_constraint": health["primary_constraint"]["label"],
            "dimension_scores": {d["key"]: d["score"] for d in health["dimensions"]
                                 if d.get("score") is not None},
        }

    return {
        "business_profile": {
            "business_type": answers.get("business_type"),
            "industry": answers.get("industry"),          # founder-editable pre-approval
            "growth_stage": answers.get("growth_stage"),
            "team_band": team_band(answers.get("team_size")),
            "revenue_band": revenue_band(answers.get("monthly_revenue")),
            "revenue_model": answers.get("revenue_model"),
        },
        "evidence_summary": {
            "kinds": {k: v for k, v in (evidence_kinds or {}).items()},
            "audit_completeness": round(
                sum(1 for q in ce.QUESTIONS if answers.get(q["id"]) not in (None, "")) / len(ce.QUESTIONS), 2),
        },
        "computed_metrics": safe_metrics,
        "contradictions": safe_contradictions,
        "observation": diagnosis or {"note": "Insufficient evidence for a diagnosis at capture time."},
        "outcome": {"status": "not_yet_observed",
                    "note": "Treatment outcome tracking begins after a treatment is applied."},
    }


def leaked_identifiers(case: dict, forbidden_terms: list[str]) -> list[str]:
    """Belt-and-braces: scan the serialized case for any forbidden string
    (org name, customer names, emails). Returns the leaks found."""
    import json
    blob = json.dumps(case, default=str).lower()
    return [t for t in forbidden_terms if t and len(t) >= 3 and t.lower() in blob]

"""
Constraint Engine V1 — deterministic, transparent, explainable.

Design contract (from the AFK Constitution):
  * No fabricated numbers. Every figure is computed from stated evidence.
  * Every conclusion carries: evidence, reasoning, confidence, missing data.
  * If evidence is insufficient the engine says so instead of guessing.

The engine is pure: answers dict in, diagnosis dict out. No DB, no I/O.
That makes it unit-testable and auditable line by line.
"""
from typing import Any, Optional

# ---------------------------------------------------------------------------
# The Revenue Audit — question schema
# Each question: id, section, label, type, options?, help?
# Question ids are the engine's evidence vocabulary.
# ---------------------------------------------------------------------------

AUDIT_SECTIONS = [
    {"id": "profile", "title": "Business Profile",
     "description": "What kind of business is this?"},
    {"id": "revenue", "title": "Revenue Model",
     "description": "How money actually comes in today."},
    {"id": "demand", "title": "Demand & Marketing",
     "description": "Where new potential customers come from."},
    {"id": "qualification", "title": "Qualification",
     "description": "How you decide which leads deserve your time."},
    {"id": "conversion", "title": "Sales & Follow-up",
     "description": "How interest becomes revenue."},
    {"id": "pricing", "title": "Pricing",
     "description": "How you charge, and how confident you are in it."},
    {"id": "retention", "title": "Customers & Retention",
     "description": "What happens after the first sale."},
    {"id": "operations", "title": "Team & Operations",
     "description": "How dependent revenue is on you personally."},
    {"id": "goals", "title": "Goals & Self-Diagnosis",
     "description": "Where you want to go and what you believe is in the way."},
]

QUESTIONS = [
    # -- profile
    {"id": "business_type", "section": "profile", "label": "Business type", "type": "select",
     "options": ["B2B services / agency", "B2B SaaS / software", "Distribution / trading", "D2C / e-commerce", "Retail / local business", "Other"]},
    {"id": "industry", "section": "profile", "label": "Industry / what you sell", "type": "text"},
    {"id": "team_size", "section": "profile", "label": "Team size (including you)", "type": "number"},
    {"id": "growth_stage", "section": "profile", "label": "Stage", "type": "select",
     "options": ["Pre-revenue", "Early revenue (finding repeatability)", "Growing (repeatable sales)", "Established (optimizing)"]},

    # -- revenue
    {"id": "monthly_revenue", "section": "revenue", "label": "Average monthly revenue (₹)", "type": "number"},
    {"id": "revenue_model", "section": "revenue", "label": "Revenue model", "type": "select",
     "options": ["One-time projects / deals", "Recurring (retainers / subscriptions)", "Repeat transactional (orders)", "Mixed"]},
    {"id": "avg_deal_value", "section": "revenue", "label": "Average deal / order value (₹)", "type": "number"},
    {"id": "revenue_goal_12m", "section": "goals", "label": "Monthly revenue target 12 months from now (₹)", "type": "number"},

    # -- demand
    {"id": "leads_per_month", "section": "demand", "label": "New leads / enquiries per month", "type": "number"},
    {"id": "lead_sources_count", "section": "demand", "label": "How many lead sources reliably produce leads?", "type": "select",
     "options": ["One", "Two or three", "Four or more"]},
    {"id": "primary_lead_source", "section": "demand", "label": "Primary lead source", "type": "select",
     "options": ["Referrals / word of mouth", "Outbound (calls, DMs, email)", "Inbound content / SEO", "Paid ads", "Partnerships / channel", "Walk-in / location"]},
    {"id": "marketing_active", "section": "demand", "label": "Is there consistent weekly marketing activity?", "type": "select",
     "options": ["Yes, systematic", "Sporadic", "No"]},

    # -- qualification
    {"id": "qualification_process", "section": "qualification", "label": "How are leads qualified before you invest time?", "type": "select",
     "options": ["No real qualification — we talk to everyone", "Informal gut-feel", "Documented criteria the team follows"]},
    {"id": "pct_leads_worth_it", "section": "qualification", "label": "Roughly what % of leads turn out to be worth the time? (%)", "type": "number"},

    # -- conversion (v2)
    {"id": "conversion_close_rate", "section": "conversion",
     "label": "Of leads you consider \"serious\", what % eventually become paying customers?", "type": "scale",
     "min": 0, "max": 100, "unit": "%"},
    {"id": "conversion_followups", "section": "conversion",
     "label": "On average, how many follow-ups do you make before giving up on a lead?", "type": "select",
     "options": ["1", "2", "3", "4–5", "6+"]},
    {"id": "conversion_owner", "section": "conversion",
     "label": "Who primarily owns follow-up and closing?", "type": "select",
     "options": ["Founder only", "Founder leads most deals", "Mostly team"]},
    {"id": "conversion_process", "section": "conversion",
     "label": "Is your sales process documented with clear stages and responsibilities?", "type": "select",
     "options": ["Fully documented + used", "Partially documented", "Mostly in people's heads"]},
    {"id": "conversion_cycle_days", "section": "conversion",
     "label": "What is the average number of days from first serious contact to payment?", "type": "number"},

    # -- pricing
    {"id": "pricing_confidence", "section": "pricing", "label": "Honest read on your pricing", "type": "select",
     "options": ["Probably underpriced", "About right", "Premium and defensible", "Honestly, no idea"]},
    {"id": "last_price_change", "section": "pricing", "label": "When did prices last change?", "type": "select",
     "options": ["Within the last year", "More than a year ago", "Never"]},
    {"id": "discounting", "section": "pricing", "label": "How often do you discount to close?", "type": "select",
     "options": ["Rarely", "Sometimes", "Most deals"]},

    # -- retention
    {"id": "repeat_rate", "section": "retention", "label": "% of customers who buy again / renew (%)", "type": "number"},
    {"id": "churn_reason_known", "section": "retention", "label": "Do you know why customers leave or don't return?", "type": "select",
     "options": ["Yes, we ask and track it", "Partially / anecdotally", "No"]},
    {"id": "retention_process", "section": "retention", "label": "Is there a deliberate process to bring customers back?", "type": "select",
     "options": ["Yes, systematic", "Ad-hoc", "None"]},

    # -- operations
    {"id": "founder_in_every_sale", "section": "operations", "label": "Is the founder personally involved in every sale?", "type": "select",
     "options": ["Yes, every deal", "Most deals", "No, the team closes independently"]},
    {"id": "documented_sales_process", "section": "operations", "label": "Is the sales process written down anywhere?", "type": "select",
     "options": ["Yes", "No"]},

    # -- goals / self-diagnosis
    {"id": "self_diagnosis", "section": "goals", "label": "In your own words: what do you believe is blocking revenue growth?", "type": "text"},
    {"id": "biggest_worry", "section": "goals", "label": "What worries you most about the next 6 months?", "type": "text"},
]

# AFK-AUD-0001 phase-b: optional context — collected but not scored until V4 penalties exist.
OPTIONAL_QUESTIONS = [
    {"id": "gross_margin_band", "section": "revenue", "label": "Typical gross margin on core offer (before overhead)", "type": "select",
     "options": ["Below 30%", "30–50%", "50–70%", "Above 70%", "Unknown"]},
    {"id": "cac_known", "section": "demand", "label": "Do you know customer acquisition cost per paying customer (₹)?", "type": "select",
     "options": ["Yes, tracked", "Rough estimate only", "No"]},
]

ALL_QUESTIONS = QUESTIONS + OPTIONAL_QUESTIONS
QUESTION_IDS = {q["id"] for q in ALL_QUESTIONS}

# Audit Science metadata (AFK-AUD-0001) — hypothesis tested per question; V4 migration status.
QUESTION_METADATA = {
    "business_type": {"hypothesis_tested": "context.segment", "evidence_class": "structure", "v4_status": "keep"},
    "leads_per_month": {"hypothesis_tested": "demand.volume", "evidence_class": "hypothesis", "v4_status": "keep"},
    "pct_leads_worth_it": {"hypothesis_tested": "qualification.filter_strength", "evidence_class": "hypothesis", "v4_status": "reframe_v4"},
    "conversion_close_rate": {"hypothesis_tested": "conversion.close_rate", "evidence_class": "hypothesis", "v4_status": "keep"},
    "conversion_process": {"hypothesis_tested": "conversion.structure", "evidence_class": "structure", "v4_status": "keep"},
    "documented_sales_process": {"hypothesis_tested": "conversion.structure", "evidence_class": "structure", "v4_status": "remove_duplicate"},
    "pricing_confidence": {"hypothesis_tested": "pricing.capture_posture", "evidence_class": "hypothesis", "v4_status": "keep"},
    "repeat_rate": {"hypothesis_tested": "retention.repeat_rate", "evidence_class": "hypothesis", "v4_status": "keep"},
    "self_diagnosis": {"hypothesis_tested": "founder.hypothesis", "evidence_class": "hypothesis", "v4_status": "move_early"},
    "gross_margin_band": {"hypothesis_tested": "pricing.capture_vs_cost", "evidence_class": "hypothesis", "v4_status": "add_v4"},
    "cac_known": {"hypothesis_tested": "demand.unit_economics_awareness", "evidence_class": "structure", "v4_status": "add_v4"},
}

# Dimension -> question ids that constitute its evidence
DIMENSIONS = {
    "demand": {
        "label": "Demand Generation",
        "fields": ["leads_per_month", "lead_sources_count", "primary_lead_source", "marketing_active"],
    },
    "qualification": {
        "label": "Lead Qualification",
        "fields": ["qualification_process", "pct_leads_worth_it"],
    },
    "conversion": {
        "label": "Sales Conversion & Follow-up",
        "fields": [
            "conversion_close_rate", "conversion_followups", "conversion_owner",
            "conversion_process", "conversion_cycle_days",
        ],
    },
    "pricing": {
        "label": "Pricing & Monetization",
        "fields": ["pricing_confidence", "last_price_change", "discounting"],
    },
    "retention": {
        "label": "Retention & Repeat Revenue",
        "fields": ["repeat_rate", "churn_reason_known", "retention_process"],
    },
    "founder_dependency": {
        "label": "Founder Dependency",
        "fields": ["founder_in_every_sale", "documented_sales_process", "team_size"],
    },
}

_QLABEL = {q["id"]: q["label"] for q in QUESTIONS}


def _num(answers: dict, key: str) -> Optional[float]:
    v = answers.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ev(answers: dict, key: str) -> dict:
    """Format one answer as a citable piece of evidence."""
    return {"question": _QLABEL.get(key, key), "answer": answers.get(key), "id": key}


MIN_DIMENSION_COVERAGE = 1.0  # Phase 1: all dimension fields required to score

_CHAIN_CAP_CRITICAL = 55  # overall health capped when any system is Critical
_CHAIN_CAP_WATCH = 70     # overall health capped when any system is Watch or worse


def _dimension_confidence(answers: dict, dim_key: str) -> float:
    fields = DIMENSIONS[dim_key]["fields"]
    answered = sum(1 for f in fields if answers.get(f) not in (None, ""))
    return round(answered / len(fields), 2) if fields else 0.0


def _dimension_scorable(conf: float) -> bool:
    return conf >= MIN_DIMENSION_COVERAGE


def _penalty_in_band(value: float, bands: list[tuple[float, float, int]]) -> int:
    """First matching [low, high) band returns its penalty."""
    for low, high, penalty in bands:
        if low <= value < high:
            return penalty
    return 0


def system_status(score: int) -> str:
    """Unified V3 status bands (100 = healthy, 0 = severe constraint)."""
    if score >= 85:
        return "Stable"
    if score >= 70:
        return "Watch"
    if score >= 55:
        return "Constrained"
    return "Critical"


def conversion_status(score: int) -> str:
    """Backward-compatible alias; maps V3 labels to conversion v2 names in tests."""
    return {
        "Stable": "Healthy",
        "Watch": "Moderate",
        "Constrained": "Pressure",
        "Critical": "Critical",
    }.get(system_status(score), "Critical")


# ---------------------------------------------------------------------------
# Rules. Each returns a list of findings:
#   {penalty, evidence: [...], reasoning: str, missing: [...]}
# Scores start at 100 per dimension; findings subtract.
# ---------------------------------------------------------------------------

def _rules_demand(a: dict) -> list[dict]:
    out = []
    leads = _num(a, "leads_per_month")
    if leads is not None:
        pen = _penalty_in_band(leads, [(0, 10, 30), (10, 20, 20), (20, 30, 10)])
        if pen:
            out.append({"penalty": pen, "evidence": [_ev(a, "leads_per_month")],
                        "reasoning": f"{int(leads)} new leads per month limits top-of-funnel capacity — downstream fixes cannot outrun thin volume."})
    if a.get("lead_sources_count") == "One":
        src = a.get("primary_lead_source", "a single source")
        out.append({"penalty": 25, "evidence": [_ev(a, "lead_sources_count"), _ev(a, "primary_lead_source")],
                    "reasoning": f"All demand depends on one source ({src}). If it slows, revenue slows with it — concentration risk, and usually a passive one."})
    if a.get("marketing_active") == "No":
        out.append({"penalty": 20, "evidence": [_ev(a, "marketing_active")],
                    "reasoning": "No consistent weekly marketing activity means lead flow is not under the business's control."})
    elif a.get("marketing_active") == "Sporadic":
        out.append({"penalty": 12, "evidence": [_ev(a, "marketing_active")],
                    "reasoning": "Sporadic marketing produces sporadic pipeline; revenue inherits the inconsistency about one sales cycle later."})
    return out


def _rules_qualification(a: dict) -> list[dict]:
    out = []
    qp = a.get("qualification_process", "")
    if qp.startswith("No real qualification"):
        out.append({"penalty": 30, "evidence": [_ev(a, "qualification_process")],
                    "reasoning": "Talking to every lead means the calendar fills with the wrong ones. Time is the scarcest asset in a founder-led sales motion."})
    elif qp == "Informal gut-feel":
        out.append({"penalty": 15, "evidence": [_ev(a, "qualification_process")],
                    "reasoning": "Qualification lives in gut-feel — wrong-fit leads still consume calendar and selling energy without a repeatable filter."})
    pct = _num(a, "pct_leads_worth_it")
    if pct is not None:
        pen = _penalty_in_band(pct, [(0, 30, 25), (30, 40, 18), (40, 50, 12)])
        if pen:
            out.append({"penalty": pen, "evidence": [_ev(a, "pct_leads_worth_it")],
                        "reasoning": f"Only ~{int(pct)}% of leads are worth the time — selling effort is spent on people who were never going to buy."})
        leads = _num(a, "leads_per_month")
        if pct < 50 and leads is not None and leads >= 10:
            out.append({"penalty": 8, "evidence": [_ev(a, "pct_leads_worth_it"), _ev(a, "leads_per_month")],
                        "reasoning": "Calendar pollution — enough lead volume that weak qualification silently taxes the whole sales motion."})
    return out


def _dimension_score(answers: dict, dim_key: str) -> int:
    return max(0, 100 - sum(f["penalty"] for f in _RULES[dim_key](answers)))


def _conversion_score(answers: dict) -> int:
    return _dimension_score(answers, "conversion")


def _rules_conversion(a: dict) -> list[dict]:
    out = []
    close = _num(a, "conversion_close_rate")
    if close is not None:
        pen = _penalty_in_band(close, [(0, 15, 30), (15, 25, 22), (25, 30, 15)])
        if pen:
            out.append({"penalty": pen, "evidence": [_ev(a, "conversion_close_rate")],
                        "reasoning": f"Only ~{int(close)}% of serious leads convert — revenue is leaking after qualification, inside follow-up or closing."})
    followups = a.get("conversion_followups", "")
    if followups in ("1", "2"):
        out.append({"penalty": 20, "evidence": [_ev(a, "conversion_followups")],
                    "reasoning": f"Giving up after {followups} follow-up{'s' if followups != '1' else ''} leaves deals unfinished; most considered purchases need sustained touches."})
    elif followups == "3":
        out.append({"penalty": 8, "evidence": [_ev(a, "conversion_followups")],
                    "reasoning": "Three follow-ups is below typical B2B persistence — deals often need more touches before a clear yes or no."})
    owner = a.get("conversion_owner", "")
    if owner in ("Founder only", "Founder leads most deals"):
        out.append({"penalty": 18, "evidence": [_ev(a, "conversion_owner")],
                    "reasoning": "Follow-up and closing depend on the founder — throughput is capped by personal bandwidth and busy weeks kill deals in progress."})
    process = a.get("conversion_process", "")
    if process == "Mostly in people's heads":
        out.append({"penalty": 15, "evidence": [_ev(a, "conversion_process")],
                    "reasoning": "The sales process lives in people's heads — it cannot be delegated, improved, or diagnosed consistently."})
    elif process == "Partially documented":
        out.append({"penalty": 8, "evidence": [_ev(a, "conversion_process")],
                    "reasoning": "Sales stages exist on paper but are not fully used — execution drift still creates inconsistent closes."})
    cycle = _num(a, "conversion_cycle_days")
    if cycle is not None and cycle > 90:
        out.append({"penalty": 10, "evidence": [_ev(a, "conversion_cycle_days")],
                    "reasoning": f"A {int(cycle)}-day sales cycle ties up capacity and increases drop-off before payment."})
    return out


_SYSTEM_FINDING_DEFAULTS = {
    "demand": {
        "finding": "Lead flow appears sufficient and diversified for the current stage.",
        "root_cause": "No major demand-generation constraint detected from your answers.",
        "business_impact": "Top-of-funnel volume is not the primary cap on revenue growth right now.",
        "expected_outcome": "Maintain source diversity and weekly marketing cadence as you scale.",
    },
    "qualification": {
        "finding": "Lead qualification is filtering the calendar effectively.",
        "root_cause": "No major qualification constraint detected from your answers.",
        "business_impact": "Selling time is concentrated on leads with reasonable fit.",
        "expected_outcome": "Sustain documented criteria so qualification does not erode as volume grows.",
    },
    "conversion": {
        "finding": "Serious interest is converting to revenue with disciplined follow-up and a usable sales process.",
        "root_cause": "No major conversion constraint detected from your answers.",
        "business_impact": "Paid revenue should track qualified demand without systematic leakage in follow-up or closing.",
        "expected_outcome": "Maintain documented stages and follow-up discipline as volume grows.",
    },
    "pricing": {
        "finding": "Pricing and discount discipline appear aligned with value capture.",
        "root_cause": "No major pricing constraint detected from your answers.",
        "business_impact": "Revenue per deal is not being silently eroded by systematic underpricing or discounting.",
        "expected_outcome": "Continue periodic price tests on new prospects to validate willingness to pay.",
    },
    "retention": {
        "finding": "Repeat revenue and retention mechanics look stable for your model.",
        "root_cause": "No major retention constraint detected from your answers.",
        "business_impact": "Growth is not fighting a leaking bucket of one-time customers.",
        "expected_outcome": "Keep tracking why customers leave so retention stays deliberate, not accidental.",
    },
    "founder_dependency": {
        "finding": "Revenue capacity is not critically bottlenecked on the founder alone.",
        "root_cause": "No major founder-dependency constraint detected from your answers.",
        "business_impact": "The business can grow without every incremental deal requiring founder hours.",
        "expected_outcome": "Document and delegate more of the sales motion as volume increases.",
    },
}


def _impact_with_revenue(answers: dict, dim_key: str, qualitative: str) -> str:
    monthly_rev = _num(answers, "monthly_revenue")
    play = _CONSTRAINT_PLAYBOOK.get(dim_key, {})
    uplift = play.get("uplift", 0)
    if not monthly_rev or not uplift:
        return qualitative
    annual = monthly_rev * 12
    low = round(annual * uplift * 0.6)
    high = round(annual * uplift * 1.3)
    return (
        f"{qualitative} Directional exposure: ₹{low:,}–₹{high:,}/yr "
        f"({int(uplift * 60)}–{int(uplift * 130)}% band around {int(uplift * 100)}% of stated annual revenue)."
    )


def build_system_finding(dim_key: str, answers: dict) -> dict:
    """Structured system finding — deterministic from stated evidence (Phase 1: all systems)."""
    findings = _RULES[dim_key](answers)
    score = _dimension_score(answers, dim_key)
    status = system_status(score)
    play = _CONSTRAINT_PLAYBOOK[dim_key]
    defaults = _SYSTEM_FINDING_DEFAULTS[dim_key]

    if not findings:
        finding = defaults["finding"]
        root_cause = defaults["root_cause"]
        impact = defaults["business_impact"]
        expected = defaults["expected_outcome"]
    else:
        finding = findings[0]["reasoning"]
        root_cause = "; ".join(f["reasoning"] for f in findings)
        impact = _impact_with_revenue(answers, dim_key, _qualitative_impact(dim_key))
        expected = _expected_outcome(dim_key)

    from backend.app.core import evidence_intel as evi  # lazy: avoids circular import

    epi = _epistemic_for_dimension(dim_key, answers)
    conf_pct = int(epi * 100)
    conf_basis = (
        f"{conf_pct}% epistemic confidence (AFK-CFM-0001) — self-report caps at "
        f"{int(evi.QUESTIONNAIRE_CEILING * 100)}% until measured evidence confirms."
    )

    formatted = (
        f"Finding:\n{finding}\n\n"
        f"Root Cause:\n{root_cause}\n\n"
        f"Business Impact:\n{impact}\n\n"
        f"Score: {score}/100 ({status})\n\n"
        f"Confidence: {conf_pct}% — {conf_basis}\n\n"
        f"Recommended Action:\n{play['next_step']}\n\n"
        f"Expected Outcome:\n{expected}"
    )

    return {
        "finding": finding,
        "root_cause": root_cause,
        "business_impact": impact,
        "score": score,
        "status": status,
        "score_line": f"Score: {score}/100 ({status})",
        "confidence": epi,
        "confidence_pct": conf_pct,
        "confidence_basis": conf_basis,
        "recommended_action": play["next_step"],
        "expected_outcome": expected,
        "formatted": formatted,
    }


def _qualitative_impact(dim_key: str) -> str:
    return {
        "demand": "Revenue growth is capped at the top of the funnel — downstream efficiency cannot compensate for thin or unreliable lead flow.",
        "qualification": "Selling capacity is consumed by wrong-fit leads — conversion and pricing work on a polluted pipeline.",
        "conversion": "Revenue is lost after leads are already serious — marketing spend and selling time do not fully convert to cash.",
        "pricing": "Margin and revenue per customer are eroding — growth requires more volume to offset weak monetization.",
        "retention": "The business refills a leaking bucket — acquisition spend fights churn instead of compounding.",
        "founder_dependency": "Revenue throughput is capped by founder hours — scale is structurally limited until knowledge is delegated.",
    }.get(dim_key, "This system is limiting overall revenue performance.")


def _expected_outcome(dim_key: str) -> str:
    return {
        "demand": "More predictable lead volume from at least one additional controlled source.",
        "qualification": "Higher share of calendar time on leads that can actually buy.",
        "conversion": "Higher close rate on existing serious leads and fewer deals dying in follow-up.",
        "pricing": "Improved revenue per deal without requiring more customers.",
        "retention": "Higher repeat revenue and clearer reasons when customers leave.",
        "founder_dependency": "More deals closed without founder presence in every step.",
    }.get(dim_key, "Measurable improvement in this system's core metric within 90 days.")


def build_conversion_system_finding(answers: dict) -> dict:
    """Backward-compatible wrapper for conversion module."""
    result = build_system_finding("conversion", answers)
    # Expose conversion v2 status labels for existing tests/UI expectations
    v2_status = conversion_status(result["score"])
    result = {**result, "status": v2_status, "score_line": f"Score: {result['score']}/100 ({v2_status})"}
    result["formatted"] = result["formatted"].replace(
        f"({result['score']}/100 ({system_status(result['score'])})".replace("Score: ", ""),
        f"Score: {result['score']}/100 ({v2_status})",
    )
    # Rebuild formatted with v2 label
    result["formatted"] = (
        f"Finding:\n{result['finding']}\n\n"
        f"Root Cause:\n{result['root_cause']}\n\n"
        f"Business Impact:\n{result['business_impact']}\n\n"
        f"Score: {result['score']}/100 ({v2_status})\n\n"
        f"Recommended Action:\n{result['recommended_action']}\n\n"
        f"Expected Outcome:\n{result['expected_outcome']}"
    )
    return result


def _rules_pricing(a: dict) -> list[dict]:
    out = []
    pc = a.get("pricing_confidence", "")
    if pc == "Probably underpriced":
        out.append({"penalty": 25, "evidence": [_ev(a, "pricing_confidence")],
                    "reasoning": "Self-admitted underpricing is the cheapest revenue fix that exists — no new leads required."})
    elif pc == "Honestly, no idea":
        out.append({"penalty": 20, "evidence": [_ev(a, "pricing_confidence")],
                    "reasoning": "Pricing has never been tested against willingness to pay; the current number is a guess carrying the whole P&L."})
    lpc = a.get("last_price_change", "")
    if lpc == "Never":
        out.append({"penalty": 15, "evidence": [_ev(a, "last_price_change")],
                    "reasoning": "Prices have never changed while costs certainly have. Margin erodes silently every year."})
    elif lpc == "More than a year ago":
        out.append({"penalty": 10, "evidence": [_ev(a, "last_price_change")],
                    "reasoning": "Prices have been static for over a year — costs and market willingness to pay have likely shifted without you noticing."})
    disc = a.get("discounting", "")
    if disc == "Most deals":
        out.append({"penalty": 20, "evidence": [_ev(a, "discounting")],
                    "reasoning": "Discounting on most deals means the list price isn't real — buyers have learned to wait for it."})
    elif disc == "Sometimes":
        out.append({"penalty": 10, "evidence": [_ev(a, "discounting")],
                    "reasoning": "Routine discounting trains buyers to negotiate — list price is not the real price."})
    if pc == "Probably underpriced" and disc in ("Sometimes", "Most deals"):
        out.append({"penalty": 8, "evidence": [_ev(a, "pricing_confidence"), _ev(a, "discounting")],
                    "reasoning": "Double monetization leak — underpriced positioning plus habitual discounting compounds margin loss."})
    if pc == "About right" and disc == "Sometimes":
        out.append({"penalty": 8, "evidence": [_ev(a, "pricing_confidence"), _ev(a, "discounting")],
                    "reasoning": "Pricing feels right on paper but routine discounting suggests list price is not what customers actually pay."})
    return out


_REPEAT_MODELS = (
    "Recurring (retainers / subscriptions)",
    "Repeat transactional (orders)",
    "Mixed",
)


def _rules_retention(a: dict) -> list[dict]:
    out = []
    rr = _num(a, "repeat_rate")
    model = a.get("revenue_model", "")
    if rr is not None and model in _REPEAT_MODELS:
        pen = _penalty_in_band(rr, [(0, 30, 30), (30, 45, 15), (45, 55, 8)])
        if pen:
            out.append({"penalty": pen, "evidence": [_ev(a, "repeat_rate"), _ev(a, "revenue_model")],
                        "reasoning": f"A ~{int(rr)}% repeat rate in a repeat-revenue model means the business refills a leaking bucket — growth spend fights churn."})
    churn = a.get("churn_reason_known", "")
    if churn == "No":
        out.append({"penalty": 20, "evidence": [_ev(a, "churn_reason_known")],
                    "reasoning": "Nobody knows why customers leave, so retention can't be fixed — only guessed at."})
    elif churn == "Partially / anecdotally":
        out.append({"penalty": 12, "evidence": [_ev(a, "churn_reason_known")],
                    "reasoning": "Churn reasons are anecdotal, not tracked — retention fixes will stay reactive."})
    rp = a.get("retention_process", "")
    if rp == "None":
        out.append({"penalty": 15, "evidence": [_ev(a, "retention_process")],
                    "reasoning": "No deliberate reason for customers to come back; repeat revenue is being left to chance."})
    elif rp == "Ad-hoc":
        out.append({"penalty": 10, "evidence": [_ev(a, "retention_process")],
                    "reasoning": "Retention is ad-hoc — repeat revenue depends on memory and goodwill, not a system."})
    return out


def _rules_founder(a: dict) -> list[dict]:
    out = []
    fie = a.get("founder_in_every_sale", "")
    team = _num(a, "team_size")
    if fie == "Yes, every deal":
        ev = [_ev(a, "founder_in_every_sale")]
        extra = ""
        if team is not None and team > 3:
            ev.append(_ev(a, "team_size"))
            extra = f" With a team of {int(team)}, the constraint is not headcount — it's that revenue knowledge lives in one person."
        out.append({"penalty": 25, "evidence": ev,
                    "reasoning": "Revenue is capped at the founder's personal hours." + extra})
    elif fie == "Most deals":
        out.append({"penalty": 15, "evidence": [_ev(a, "founder_in_every_sale")],
                    "reasoning": "The founder is still in most deals — delegation is partial and throughput remains person-bound."})
    if a.get("documented_sales_process") == "No":
        out.append({"penalty": 15, "evidence": [_ev(a, "documented_sales_process")],
                    "reasoning": "An undocumented sales process can't be delegated, improved, or diagnosed — it can only be performed."})
    if fie in ("Yes, every deal", "Most deals") and a.get("conversion_owner", "").startswith("Founder"):
        out.append({"penalty": 8, "evidence": [_ev(a, "founder_in_every_sale"), _ev(a, "conversion_owner")],
                    "reasoning": "Structural ceiling — founder owns both pipeline presence and follow-up/closing; revenue cannot scale past personal bandwidth."})
    return out


def _epistemic_for_dimension(
    dim_key: str,
    answers: dict,
    kinds_present: dict[str, int] | None = None,
    quality_by_kind: dict[str, float] | None = None,
) -> float:
    """Per-dimension epistemic confidence per AFK-CFM-0001."""
    from backend.app.core import evidence_intel as evi  # lazy: avoids circular import

    breakdown = evi.evidence_confidence(
        answers,
        kinds_present or {},
        quality_by_kind or {},
    )
    return breakdown["per_dimension"].get(dim_key, 0.0)


def _apply_epistemic_confidence(
    dims_out: list[dict],
    answers: dict,
    kinds_present: dict[str, int] | None = None,
    quality_by_kind: dict[str, float] | None = None,
) -> dict:
    """Replace misleading coverage-as-confidence with CFM-0001 epistemic values."""
    from backend.app.core import evidence_intel as evi  # lazy: avoids circular import

    breakdown = evi.evidence_confidence(
        answers,
        kinds_present or {},
        quality_by_kind or {},
    )
    for d in dims_out:
        d["confidence"] = breakdown["per_dimension"].get(d["key"], 0.0)
    return breakdown


def _funnel_coherence_check(answers: dict) -> dict | None:
    """Deterministic funnel arithmetic — flags belief/evidence incoherence (TOC-style)."""
    leads = _num(answers, "leads_per_month")
    worth = _num(answers, "pct_leads_worth_it")
    close = _num(answers, "conversion_close_rate")
    deal = _num(answers, "avg_deal_value")
    stated = _num(answers, "monthly_revenue")
    if None in (leads, worth, close, deal, stated) or stated <= 0:
        return None

    serious = leads * (worth / 100.0)
    new_payers = serious * (close / 100.0)
    theoretical = new_payers * deal
    ratio = theoretical / stated

    if 0.55 <= ratio <= 1.6:
        return None

    if ratio < 0.55:
        explanation = (
            f"Stated revenue (₹{int(stated):,}/mo) is much higher than a first-order funnel estimate "
            f"(₹{int(theoretical):,}/mo from leads × worth-it% × close% × deal size). "
            "Repeat revenue, upsells, or misstated funnel numbers may explain the gap — but the stated story does not close arithmetically."
        )
    else:
        explanation = (
            f"Funnel arithmetic (₹{int(theoretical):,}/mo) exceeds stated revenue (₹{int(stated):,}/mo). "
            "Either revenue is under-reported or funnel inputs are overstated."
        )

    return {
        "theoretical_monthly_revenue": round(theoretical),
        "stated_monthly_revenue": round(stated),
        "ratio": round(ratio, 2),
        "verdict": "incoherent",
        "explanation": explanation,
        "basis": (
            f"{int(leads)} leads × {int(worth)}% worth-it × {int(close)}% close × "
            f"₹{int(deal):,} deal ≈ ₹{int(theoretical):,}/mo vs stated ₹{int(stated):,}/mo."
        ),
    }


_HYPOTHESIS_SIGNALS = {
    "demand": ("lead", "pipeline", "marketing", "enquir", "inbound", "outbound", "referral"),
    "qualification": ("qualif", "wrong lead", "wrong-fit", "calendar"),
    "conversion": ("close", "follow", "sales", "convert", "win rate"),
    "pricing": ("price", "pricing", "margin", "discount", "underpric"),
    "retention": ("churn", "retention", "repeat", "renew", "leak"),
    "founder_dependency": ("founder", "my time", "delegat", "team", "hire"),
}


def _hypothesis_verdict(answers: dict, primary_key: str) -> dict | None:
    """Cross-examine founder self-diagnosis against measured primary constraint."""
    text = (answers.get("self_diagnosis") or "").lower().strip()
    if not text or not primary_key:
        return None

    def _signals(dim: str) -> bool:
        return any(s in text for s in _HYPOTHESIS_SIGNALS.get(dim, ()))

    believed = next((k for k in _HYPOTHESIS_SIGNALS if _signals(k)), None)
    if not believed:
        return {
            "founder_hypothesis": answers.get("self_diagnosis"),
            "inferred_belief_system": None,
            "measured_primary": primary_key,
            "verdict": "unclear",
            "explanation": "Could not map your hypothesis to a revenue system — compare it manually to the measured primary constraint.",
        }

    if believed == primary_key:
        return {
            "founder_hypothesis": answers.get("self_diagnosis"),
            "inferred_belief_system": believed,
            "measured_primary": primary_key,
            "verdict": "aligned",
            "explanation": f"Your hypothesis aligns with the measured primary constraint ({DIMENSIONS[primary_key]['label']}).",
        }

    return {
        "founder_hypothesis": answers.get("self_diagnosis"),
        "inferred_belief_system": believed,
        "measured_primary": primary_key,
        "verdict": "contradicted",
        "explanation": (
            f"You pointed to {DIMENSIONS[believed]['label'].lower()}, but evidence ranks "
            f"{DIMENSIONS[primary_key]['label'].lower()} as the stronger constraint right now."
        ),
    }


def _compound_findings(answers: dict, dims: list[dict]) -> list[dict]:
    """Cross-system interactions — evaluated from KB compound_pattern catalog."""
    from backend.app.knowledge_engine.compound_runtime import evaluate_compound_findings
    return evaluate_compound_findings(answers, dims)


_RULES = {
    "demand": _rules_demand,
    "qualification": _rules_qualification,
    "conversion": _rules_conversion,
    "pricing": _rules_pricing,
    "retention": _rules_retention,
    "founder_dependency": _rules_founder,
}

# Constraint -> next step + opportunity heuristic (uplift fraction of annual revenue, shown with formula)
# fixability / time_to_impact_days: operator-judgment metadata for impact priority (uncalibrated).
PRIORITY_MODEL_ID = "AFK-PRI-0001"

_FIXABILITY_FACTOR = {"high": 1.0, "medium": 0.85, "low": 0.70}
_TIME_IMPACT_FACTOR = {30: 1.0, 60: 0.9, 90: 0.8}

def _priority_adjunct_config() -> dict:
    try:
        from backend.app.knowledge_engine.kb_runtime import priority_adjunct_config
        return priority_adjunct_config()
    except Exception:
        return {
            "pricing_discount_threshold_pct": 5.0,
            "pricing_discount_slope": 2.0,
            "pricing_discount_cap": 2.0,
            "retention_repeat_gap_pp": 20.0,
            "retention_repeat_slope": 3.0,
            "retention_repeat_cap": 1.75,
        }


def compute_evidence_priority_adjustments(
    metrics: dict | None,
    answers: dict | None = None,
) -> dict[str, dict]:
    """Measured-evidence multipliers for priority — never applied without uploaded metrics."""
    if not metrics:
        return {}
    cfg = _priority_adjunct_config()
    out = {}
    thresh = cfg["pricing_discount_threshold_pct"]
    disc = metrics.get("avg_discount_pct")
    if disc and disc.get("value") is not None:
        pct = float(disc["value"])
        if pct >= thresh:
            boost = min(
                cfg["pricing_discount_cap"],
                (pct - thresh) / cfg["pricing_discount_slope"],
            )
            mult = round(1 + boost, 3)
            out["pricing"] = {
                "exposure_multiplier": mult,
                "source_metric": "avg_discount_pct",
                "source_value": pct,
                "threshold_pct": thresh,
                "basis": (
                    f"Invoice evidence: average discount {pct}% exceeds {thresh}% "
                    f"threshold — pricing revenue exposure ×{mult} (AFK-PRI-0001 evidence adjunct). "
                    "Slope is operator judgment calibrated against AFK-CAS-0001; not an industry benchmark."
                ),
            }

    stated_rr = _num(answers or {}, "repeat_rate")
    measured = metrics.get("repeat_customer_rate")
    if stated_rr is not None and measured and measured.get("value") is not None:
        actual = float(measured["value"])
        gap = abs(stated_rr - actual)
        if gap >= cfg["retention_repeat_gap_pp"]:
            boost = min(cfg["retention_repeat_cap"] - 1.0, gap / cfg["retention_repeat_slope"])
            mult = round(1 + boost, 3)
            out["retention"] = {
                "exposure_multiplier": mult,
                "source_metric": "repeat_customer_rate",
                "source_value": actual,
                "stated_value": stated_rr,
                "gap_pp": round(gap, 1),
                "basis": (
                    f"Invoice evidence: measured repeat customer rate {actual}% vs stated {int(stated_rr)}% "
                    f"(gap {int(gap)}pp) — retention exposure ×{mult}. "
                    "Applied only when uploaded invoices contradict self-report."
                ),
            }
    return out


def build_science_provenance(kb_release: str | None = None) -> dict:
    """Version tags for reproducible diagnosis — AFK moat: scientific versioning."""
    from backend.app.knowledge_engine.rule_provenance import RULE_PACK_ID
    from backend.app.knowledge_engine.compound_runtime import COMPOUND_PACK_ID
    return {
        "engine_version": "bse-1.0.0",
        "kb_release": kb_release or "registry-live",
        "confidence_model_id": "AFK-CFM-0001",
        "priority_model_id": PRIORITY_MODEL_ID,
        "validation_protocol_id": "AFK-VAL-0001",
        "audit_spec_id": "AFK-AUD-0001",
        "rule_pack": RULE_PACK_ID,
        "compound_pack": COMPOUND_PACK_ID,
        "note": "Findings cite AFK-DET-* via rule_provenance; compounds cite AFK-CMP-* via compound_runtime.",
    }

_CONSTRAINT_PLAYBOOK = {
    "demand": {
        "next_step": "Before spending on ads: pick ONE additional lead source that matches how your customers already buy, and commit to it for 30 days. Volume is the cap right now — nothing downstream can compensate.",
        "uplift": 0.15,
        "fixability": "medium",
        "time_to_impact_days": 60,
    },
    "qualification": {
        "next_step": "Write down 3 disqualifying questions and ask them in the first conversation. The goal this month is fewer conversations, not more.",
        "uplift": 0.08,
        "fixability": "high",
        "time_to_impact_days": 30,
    },
    "conversion": {
        "next_step": "Install a dead-simple follow-up system this week: every open lead gets a next-touch date, and no lead is closed-lost before 5 touches. This is the highest-leverage fix because the leads are already paid for.",
        "uplift": 0.20,
        "fixability": "high",
        "time_to_impact_days": 30,
    },
    "pricing": {
        "next_step": "Quote 15–20% higher to the next three NEW prospects only. Existing customers unchanged. You are buying information about willingness to pay for the price of three conversations.",
        "uplift": 0.12,
        "fixability": "medium",
        "time_to_impact_days": 30,
    },
    "retention": {
        "next_step": "Call five customers who stopped buying and ask one question: 'what changed?' Do not sell on the call. Their answers are the retention strategy.",
        "uplift": 0.18,
        "fixability": "medium",
        "time_to_impact_days": 60,
    },
    "founder_dependency": {
        "next_step": "Record yourself on the next three sales calls, then write the one-page playbook of what actually happens. You can't delegate what isn't written down.",
        "uplift": 0.10,
        "fixability": "low",
        "time_to_impact_days": 90,
    },
}


def compute_constraint_priority(
    dim_key: str,
    score: int,
    evidence_adjustments: dict[str, dict] | None = None,
) -> dict:
    """Impact-weighted constraint priority (DIAGNOSTIC_REDESIGN_V3 §8).

    priority = severity × revenue_exposure × fixability × time_factor
    where severity = (100 − score) / 100 and revenue_exposure proxies to playbook uplift.
    Optional evidence_adjustments multiply exposure when uploaded metrics justify it."""
    play = _CONSTRAINT_PLAYBOOK.get(dim_key, {})
    severity = (100 - score) / 100.0
    exposure = play.get("uplift", 0.10)
    fix = _FIXABILITY_FACTOR.get(play.get("fixability", "medium"), 0.85)
    time_days = play.get("time_to_impact_days", 60)
    time_f = _TIME_IMPACT_FACTOR.get(time_days, 0.9)
    adj = (evidence_adjustments or {}).get(dim_key, {})
    mult = adj.get("exposure_multiplier", 1.0)
    effective_exposure = exposure * mult
    priority = severity * effective_exposure * fix * time_f
    result = {
        "model_id": PRIORITY_MODEL_ID,
        "priority_score": round(priority, 4),
        "severity_index": round(severity * 100, 1),
        "revenue_exposure": exposure,
        "effective_revenue_exposure": round(effective_exposure, 4),
        "fixability": fix,
        "fixability_label": play.get("fixability", "medium"),
        "time_to_impact_days": time_days,
        "formula": (
            "(100 − score) / 100 × uplift_heuristic × fixability × time_factor"
            + (" × evidence_exposure_multiplier" if mult != 1.0 else "")
            + " — operator-judgment weights unless evidence multiplier applied."
        ),
    }
    if mult != 1.0:
        result["evidence_adjustment"] = adj
    return result


def _select_primary_constraint(
    scored: list[dict],
    evidence_adjustments: dict[str, dict] | None = None,
) -> tuple[dict, dict, list[dict]]:
    """Pick primary by impact priority; tie-break on lower dimension score."""
    lowest = min(scored, key=lambda d: d["score"])
    ranking = []
    for d in scored:
        pri = compute_constraint_priority(d["key"], d["score"], evidence_adjustments)
        ranking.append({
            "key": d["key"],
            "label": d["label"],
            "score": d["score"],
            "confidence": d["confidence"],
            **pri,
        })
    ranking.sort(key=lambda x: (-x["priority_score"], x["score"]))
    primary_key = ranking[0]["key"]
    primary = next(d for d in scored if d["key"] == primary_key)
    return primary, lowest, ranking


def compute_twin(answers: dict) -> dict:
    """The Business Twin: structured understanding, not AI output.
    Directly restates the founder's evidence in profile form."""
    def has(k):
        return answers.get(k) not in (None, "")

    known = [q for q in QUESTIONS if has(q["id"])]
    completeness = round(len(known) / len(QUESTIONS), 2)

    diagnosis = compute_health(answers)
    constraints = [
        {"dimension": d["label"], "score": d["score"]}
        for d in diagnosis.get("dimensions", [])
        if d.get("score") is not None and d["score"] <= 60
    ]
    strengths = [
        {"dimension": d["label"], "score": d["score"]}
        for d in diagnosis.get("dimensions", [])
        if d.get("score") is not None and d["score"] >= 80
        and _dimension_scorable(d.get("coverage", 0))
    ]

    return {
        "profile": {
            "business_type": answers.get("business_type"),
            "industry": answers.get("industry"),
            "growth_stage": answers.get("growth_stage"),
            "team_size": answers.get("team_size"),
            "revenue_model": answers.get("revenue_model"),
            "monthly_revenue": answers.get("monthly_revenue"),
            "avg_deal_value": answers.get("avg_deal_value"),
            "primary_lead_source": answers.get("primary_lead_source"),
            "sales_motion": answers.get("founder_in_every_sale"),
            "pricing_posture": answers.get("pricing_confidence"),
            "revenue_goal_12m": answers.get("revenue_goal_12m"),
        },
        "self_diagnosis": answers.get("self_diagnosis"),
        "biggest_worry": answers.get("biggest_worry"),
        "constraints": constraints,
        "strengths": strengths,
        "completeness": completeness,
        "fields_answered": len(known),
        "fields_total": len(QUESTIONS),
    }


def compute_health(
    answers: dict,
    evidence_kinds: dict[str, int] | None = None,
    evidence_quality: dict[str, float] | None = None,
    evidence_metrics: dict | None = None,
) -> dict:
    """Full diagnosis. Returns either sufficient=False with what's missing,
    or the health score + per-dimension findings, all evidence-cited."""
    dims_out = []
    total_conf_weight = 0.0
    weighted_score = 0.0

    for key, meta in DIMENSIONS.items():
        coverage = _dimension_confidence(answers, key)
        missing = [_QLABEL[f] for f in meta["fields"] if answers.get(f) in (None, "")]
        findings = _RULES[key](answers) if coverage > 0 else []
        if findings:
            from backend.app.knowledge_engine.rule_provenance import annotate_findings
            annotate_findings(findings, key)
        score = None
        if _dimension_scorable(coverage):
            score = max(0, 100 - sum(f["penalty"] for f in findings))
            weighted_score += score * coverage
            total_conf_weight += coverage
        dims_out.append({
            "key": key,
            "label": meta["label"],
            "score": score,
            "coverage": coverage,
            "confidence": coverage,  # replaced with epistemic below
            "findings": findings,
            "missing": missing,
        })

    answered = sum(1 for q in QUESTIONS if answers.get(q["id"]) not in (None, ""))
    completeness = round(answered / len(QUESTIONS), 2)

    if total_conf_weight == 0 or completeness < 0.35:
        return {
            "sufficient": False,
            "completeness": completeness,
            "message": "Not enough evidence to diagnose. Complete more of the Revenue Audit — the engine will not guess.",
            "dimensions": dims_out,
            "missing_summary": [d["label"] for d in dims_out if not _dimension_scorable(d["coverage"])],
        }

    epi_breakdown = _apply_epistemic_confidence(
        dims_out, answers, evidence_kinds, evidence_quality,
    )
    health = round(weighted_score / total_conf_weight)
    scored = [d for d in dims_out if d["score"] is not None]
    priority_adjustments = compute_evidence_priority_adjustments(evidence_metrics, answers)
    primary, lowest_scored, priority_ranking = _select_primary_constraint(scored, priority_adjustments)
    primary_priority = compute_constraint_priority(
        primary["key"], primary["score"], priority_adjustments,
    )
    selection_method = (
        "impact_priority_evidence_adjusted" if priority_adjustments else "impact_priority"
    )
    overall_conf = epi_breakdown["overall"]

    weakest = min(d["score"] for d in scored) if scored else health
    if weakest <= _CHAIN_CAP_CRITICAL:
        health = min(health, _CHAIN_CAP_CRITICAL)
    elif weakest <= _CHAIN_CAP_WATCH:
        health = min(health, _CHAIN_CAP_WATCH)
    if any(system_status(d["score"]) == "Critical" for d in scored):
        risk = "High Risk"
    elif health >= 75 and weakest >= 70:
        risk = "Low Risk"
    elif health >= 55:
        risk = "Moderate Risk"
    else:
        risk = "High Risk"

    compound = _compound_findings(answers, dims_out)

    # Revenue opportunity: only when revenue evidence exists. Formula shown.
    opportunity = None
    monthly_rev = _num(answers, "monthly_revenue")
    play = _CONSTRAINT_PLAYBOOK.get(primary["key"])
    if monthly_rev and play:
        annual = monthly_rev * 12
        low = round(annual * play["uplift"] * 0.6)
        high = round(annual * play["uplift"] * 1.3)
        opportunity = {
            "amount": round(annual * play["uplift"]),
            "amount_low": low,
            "amount_high": high,
            "basis": (f"Directional range: {int(play['uplift'] * 60)}–{int(play['uplift'] * 130)}% band around "
                      f"{int(play['uplift'] * 100)}% of stated annual revenue (₹{int(monthly_rev):,}/mo × 12). "
                      f"A heuristic tied to the primary constraint, not a prediction."),
        }

    return {
        "sufficient": True,
        "health_score": health,
        "risk_level": risk,
        "confidence": overall_conf,
        "completeness": completeness,
        "primary_constraint": {
            "key": primary["key"],
            "label": primary["label"],
            "score": primary["score"],
            "confidence": primary["confidence"],
            "findings": primary["findings"],
            "selection_method": selection_method,
            "priority": primary_priority,
            "lowest_score_key": lowest_scored["key"],
            "lowest_score_label": lowest_scored["label"],
            "lowest_score": lowest_scored["score"],
            "overrides_lowest_score": primary["key"] != lowest_scored["key"],
        },
        "constraint_priority_ranking": priority_ranking,
        "priority_evidence_adjustments": priority_adjustments or None,
        "science_provenance": build_science_provenance(),
        "revenue_opportunity": opportunity,
        "recommended_next_step": play["next_step"] if play else None,
        "dimensions": sorted(dims_out, key=lambda d: (d["score"] is None, d["score"] if d["score"] is not None else 0)),
        "missing_summary": [d["label"] for d in dims_out if not _dimension_scorable(d["coverage"])],
        "compound_findings": compound,
        "weakest_system_score": weakest,
        "funnel_coherence": _funnel_coherence_check(answers),
        "hypothesis_verdict": _hypothesis_verdict(answers, primary["key"]),
        "epistemic_confidence": epi_breakdown,
        "method_note": ("Scores are rule-based and deterministic. Every dimension starts at 100; each finding "
                        "subtracts a stated penalty, and every finding cites the answers it is based on. "
                        "A system scores only when 100% of its evidence fields are answered. "
                        "Epistemic confidence follows AFK-CFM-0001 (questionnaire caps at 40%). "
                        f"Primary constraint ranked by {PRIORITY_MODEL_ID}. "
                        "Overall health is capped when any system is Critical (<55)."),
    }


# ---------------------------------------------------------------------------
# M2.1 — Founder Experience layer. All derived, nothing invented.
# ---------------------------------------------------------------------------

_SOURCE_ENGINE = {
    "Referrals / word of mouth": "Referral-driven",
    "Outbound (calls, DMs, email)": "Outbound",
    "Inbound content / SEO": "Inbound",
    "Paid ads": "Paid acquisition",
    "Partnerships / channel": "Channel / partnerships",
    "Walk-in / location": "Location-driven",
}


def compute_dna(answers: dict) -> list[dict]:
    """Business DNA: six traits, each derived from named evidence.
    Traits without evidence say so instead of guessing."""
    def trait(label, value, source_field):
        return {
            "label": label,
            "value": value if value else "Unknown — not enough evidence",
            "known": bool(value),
            "source": _QLABEL.get(source_field, source_field) if value else None,
        }

    fie = answers.get("founder_in_every_sale")
    growth_style = {"Yes, every deal": "Founder-led", "Most deals": "Founder-heavy",
                    "No, the team closes independently": "Team-driven"}.get(fie)

    engine_v = _SOURCE_ENGINE.get(answers.get("primary_lead_source"))

    adv, cyc = _num(answers, "avg_deal_value"), _num(answers, "conversion_cycle_days")
    sales_motion = None
    if adv is not None or cyc is not None:
        sales_motion = "Consultative" if ((adv or 0) >= 100000 or (cyc or 0) >= 21) else "Transactional"

    decision_speed = None
    if cyc is not None:
        decision_speed = "Fast (≤1 week)" if cyc <= 7 else ("Moderate (≤1 month)" if cyc <= 30 else "Long-cycle")

    return [
        trait("Growth Style", growth_style, "founder_in_every_sale"),
        trait("Revenue Engine", engine_v, "primary_lead_source"),
        trait("Sales Motion", sales_motion, "avg_deal_value"),
        trait("Decision Speed", decision_speed, "conversion_cycle_days"),
        trait("Pricing Posture", answers.get("pricing_confidence"), "pricing_confidence"),
        trait("Current Maturity", answers.get("growth_stage"), "growth_stage"),
    ]


def compute_narrative(answers: dict, org_name: str = None) -> Optional[str]:
    """Analyst-voice business summary composed deterministically from answers.
    Returns None when there isn't enough to say anything defensible."""
    h = compute_health(answers)
    if not h.get("sufficient"):
        return None

    name = org_name or "This company"
    parts = []

    bt = answers.get("business_type")
    stage = answers.get("growth_stage")
    fie = answers.get("founder_in_every_sale")
    lead = ("founder-led " if fie == "Yes, every deal" else "")
    bt_txt = bt.split(" / ")[0] if bt else "business"
    if bt_txt not in ("B2B services", "B2B SaaS", "D2C"):
        bt_txt = bt_txt.lower()
    s1 = f"{name} is a {lead}{bt_txt} business"
    ind = answers.get("industry")
    if ind:
        s1 += f" in {ind.lower()}" if len(str(ind)) < 60 else ""
    model = answers.get("revenue_model")
    if model:
        model_txt = {"One-time projects / deals": "one-time project revenue",
                     "Recurring (retainers / subscriptions)": "recurring revenue",
                     "Repeat transactional (orders)": "repeat order revenue",
                     "Mixed": "a mix of recurring and one-time revenue"}.get(model, model.lower())
        s1 += f", earning {model_txt}"
    s1 += f", currently at the '{stage.lower()}' stage." if stage else "."
    parts.append(s1)

    src = answers.get("primary_lead_source")
    conc = answers.get("lead_sources_count") == "One"
    if src:
        s2 = f"Growth currently depends {'entirely' if conc else 'primarily'} on {src.lower()}"
        s2 += " — a single channel the business does not directly control." if (conc and "Referrals" in src) else "."
        parts.append(s2)

    scored = [d for d in h["dimensions"] if d["score"] is not None]
    if scored:
        strong = [d["label"] for d in scored if d["score"] >= 80]
        weak = [d["label"] for d in scored if d["score"] <= 60]
        if strong and weak:
            parts.append(f"{', '.join(strong)} {'looks' if len(strong) == 1 else 'look'} healthy, "
                         f"but {' and '.join(w.lower() for w in weak)} {'is' if len(weak) == 1 else 'are'} limiting revenue growth.")
        elif weak:
            parts.append(f"The main pressure points are {' and '.join(w.lower() for w in weak)}.")

        demand_d = next((d for d in scored if d["key"] == "demand"), None)
        commercial = [d for d in scored if d["key"] in ("conversion", "pricing", "qualification")]
        if demand_d and commercial:
            comm_avg = sum(d["score"] for d in commercial) / len(commercial)
            if demand_d["score"] >= 70 and comm_avg < demand_d["score"]:
                parts.append("Overall, the business appears constrained by commercial execution rather than demand.")
            elif demand_d["score"] < 60 <= comm_avg:
                parts.append("Overall, the business appears constrained by demand generation rather than its ability to close and keep customers.")
            else:
                parts.append(f"Overall Revenue Health stands at {h['health_score']}/100 ({h['risk_level'].lower()}).")
    return " ".join(parts)


_CONSTRAINT_PROBES = {
    "demand": ["Which single new lead source is most natural for how your customers already buy?",
               "How many leads did the best month in the last year produce, and what caused it?"],
    "qualification": ["What are the 3 signs a lead will waste your time — the ones you notice too late?",
                      "What % of your calendar last week went to leads who were never going to buy?"],
    "conversion": ["What are the top 3 reasons deals are lost?",
                   "How many open leads right now have no scheduled next touch?"],
    "pricing": ["When did you last quote a higher price to a brand-new prospect, and what happened?",
                "What is your customer acquisition cost?"],
    "retention": ["What did the last 5 customers who left say — or were they never asked?",
                  "What % of revenue comes from customers older than 12 months?"],
    "founder_dependency": ["If you took 2 weeks off, which part of the sales process breaks first?",
                           "What would a new hire need to know to close a deal without you in the room?"],
}


_OPTIONAL_EVIDENCE_PROMPTS: dict[str, dict[str, str]] = {
    "gross_margin_band": {
        "Unknown": "What is your typical gross margin on your core offer? A P&L or unit-cost breakdown would sharpen monetization diagnosis.",
        "Below 30%": "Thin margins amplify pricing pressure — can you share unit economics (COGS vs price) for your core offer?",
    },
    "cac_known": {
        "No": "What did you spend on marketing and sales last quarter, and how many new paying customers resulted? CAC unlocks demand ROI diagnosis.",
        "Rough estimate only": "Refine CAC with tracked spend ÷ new customers — even one quarter of data sharpens demand priority.",
    },
}


def compute_open_questions(answers: dict) -> list[str]:
    """Questions AFK still has: unanswered audit fields first (real gaps),
    optional-field evidence prompts, then constraint-specific probes. Max 5."""
    h = compute_health(answers)
    out = []
    # Real evidence gaps, most-impactful dimensions first
    for d in h["dimensions"]:
        for m in d.get("missing", []):
            q = f"{m}?" if not m.endswith("?") else m
            if q not in out:
                out.append(q)
    # Optional V4 fields — evidence prompts when answer signals uncertainty
    for field_id, by_answer in _OPTIONAL_EVIDENCE_PROMPTS.items():
        ans = answers.get(field_id)
        if ans in by_answer:
            prompt = by_answer[ans]
            if prompt not in out:
                out.append(prompt)
    # Constraint probes
    if h.get("sufficient"):
        for probe in _CONSTRAINT_PROBES.get(h["primary_constraint"]["key"], []):
            if probe not in out:
                out.append(probe)
    return out[:5]


def evidence_stats(answers: dict) -> dict:
    """Real counts only — what the diagnosis is actually built from."""
    h = compute_health(answers)
    answered = sum(1 for q in QUESTIONS if answers.get(q["id"]) not in (None, ""))
    findings = sum(len(d["findings"]) for d in h["dimensions"])
    citations = sum(len(f["evidence"]) for d in h["dimensions"] for f in d["findings"])
    scored_dims = sum(1 for d in h["dimensions"] if d["score"] is not None)
    return {
        "audit_answers": answered,
        "findings": findings,
        "evidence_citations": citations,
        "dimensions_analyzed": scored_dims,
        "dimensions_total": len(DIMENSIONS),
        "total_points": answered + citations,
    }


def compute_recommendation(answers: dict) -> Optional[dict]:
    """The single next best action as a trust card:
    evidence / confidence / assumptions / expected impact."""
    h = compute_health(answers)
    if not h.get("sufficient"):
        return None
    pc = h["primary_constraint"]
    play = _CONSTRAINT_PLAYBOOK.get(pc["key"], {})
    top = pc["findings"][0] if pc["findings"] else None
    return {
        "action": play.get("next_step"),
        "constraint": pc["label"],
        "why": (
            top["reasoning"] if top else (
                f"Impact priority ranks {pc['label']} above "
                f"{pc.get('lowest_score_label', 'other systems')} despite a higher dimension score — "
                "revenue exposure and fixability outweigh raw severity."
                if pc.get("overrides_lowest_score") else
                "This dimension ranks highest on impact-weighted priority among all measured dimensions."
            )
        ),
        "evidence": [e for f in pc["findings"] for e in f["evidence"]],
        "confidence_pct": int(pc["confidence"] * 100),
        "confidence_basis": (
            f"Based on {int(pc['confidence'] * 100)}% epistemic confidence (AFK-CFM-0001) for "
            f"{pc['label']} and deterministic scoring rules."
        ),
        "assumptions": ("Assumes stated audit answers are accurate, and that the uplift heuristic "
                        f"({int(play.get('uplift', 0) * 100)}% of annual revenue) transfers to this business — "
                        "unvalidated until tested."),
        "expected_impact": "High" if play.get("uplift", 0) >= 0.15 else "Medium",
    }

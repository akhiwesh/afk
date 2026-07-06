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

QUESTION_IDS = {q["id"] for q in QUESTIONS}

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


def _dimension_confidence(answers: dict, dim_key: str) -> float:
    fields = DIMENSIONS[dim_key]["fields"]
    answered = sum(1 for f in fields if answers.get(f) not in (None, ""))
    return round(answered / len(fields), 2) if fields else 0.0


# ---------------------------------------------------------------------------
# Rules. Each returns a list of findings:
#   {penalty, evidence: [...], reasoning: str, missing: [...]}
# Scores start at 100 per dimension; findings subtract.
# ---------------------------------------------------------------------------

def _rules_demand(a: dict) -> list[dict]:
    out = []
    leads = _num(a, "leads_per_month")
    if leads is not None and leads < 10:
        out.append({"penalty": 30, "evidence": [_ev(a, "leads_per_month")],
                    "reasoning": f"{int(leads)} new leads per month is a thin top of funnel. Almost any downstream improvement is capped by this volume."})
    if a.get("lead_sources_count") == "One":
        src = a.get("primary_lead_source", "a single source")
        out.append({"penalty": 25, "evidence": [_ev(a, "lead_sources_count"), _ev(a, "primary_lead_source")],
                    "reasoning": f"All demand depends on one source ({src}). If it slows, revenue slows with it — concentration risk, and usually a passive one."})
    if a.get("marketing_active") == "No":
        out.append({"penalty": 20, "evidence": [_ev(a, "marketing_active")],
                    "reasoning": "No consistent weekly marketing activity means lead flow is not under the business's control."})
    elif a.get("marketing_active") == "Sporadic":
        out.append({"penalty": 10, "evidence": [_ev(a, "marketing_active")],
                    "reasoning": "Sporadic marketing produces sporadic pipeline; revenue inherits the inconsistency about one sales cycle later."})
    return out


def _rules_qualification(a: dict) -> list[dict]:
    out = []
    if a.get("qualification_process", "").startswith("No real qualification"):
        out.append({"penalty": 30, "evidence": [_ev(a, "qualification_process")],
                    "reasoning": "Talking to every lead means the calendar fills with the wrong ones. Time is the scarcest asset in a founder-led sales motion."})
    pct = _num(a, "pct_leads_worth_it")
    if pct is not None and pct < 30:
        out.append({"penalty": 25, "evidence": [_ev(a, "pct_leads_worth_it")],
                    "reasoning": f"Only ~{int(pct)}% of leads are worth the time — most selling effort is spent on people who were never going to buy."})
    return out


def conversion_status(score: int) -> str:
    """Conversion System v2 status bands."""
    if score >= 85:
        return "Healthy"
    if score >= 70:
        return "Moderate"
    if score >= 55:
        return "Pressure"
    return "Critical"


def _conversion_score(answers: dict) -> int:
    return max(0, 100 - sum(f["penalty"] for f in _rules_conversion(answers)))


def _rules_conversion(a: dict) -> list[dict]:
    out = []
    close = _num(a, "conversion_close_rate")
    if close is not None and close < 30:
        out.append({"penalty": 22, "evidence": [_ev(a, "conversion_close_rate")],
                    "reasoning": f"Only ~{int(close)}% of serious leads convert — revenue is leaking after qualification, inside follow-up or closing."})
    followups = a.get("conversion_followups", "")
    if followups in ("1", "2"):
        out.append({"penalty": 20, "evidence": [_ev(a, "conversion_followups")],
                    "reasoning": f"Giving up after {followups} follow-up{'s' if followups != '1' else ''} leaves deals unfinished; most considered purchases need sustained touches."})
    owner = a.get("conversion_owner", "")
    if owner in ("Founder only", "Founder leads most deals"):
        out.append({"penalty": 18, "evidence": [_ev(a, "conversion_owner")],
                    "reasoning": "Follow-up and closing depend on the founder — throughput is capped by personal bandwidth and busy weeks kill deals in progress."})
    process = a.get("conversion_process", "")
    if process == "Mostly in people's heads":
        out.append({"penalty": 15, "evidence": [_ev(a, "conversion_process")],
                    "reasoning": "The sales process lives in people's heads — it cannot be delegated, improved, or diagnosed consistently."})
    cycle = _num(a, "conversion_cycle_days")
    if cycle is not None and cycle > 90:
        out.append({"penalty": 10, "evidence": [_ev(a, "conversion_cycle_days")],
                    "reasoning": f"A {int(cycle)}-day sales cycle ties up capacity and increases drop-off before payment."})
    return out


def build_conversion_system_finding(answers: dict) -> dict:
    """Structured Conversion System v2 finding — deterministic from stated evidence."""
    findings = _rules_conversion(answers)
    score = _conversion_score(answers)
    status = conversion_status(score)
    play = _CONSTRAINT_PLAYBOOK["conversion"]

    if not findings:
        finding = "Serious interest is converting to revenue with disciplined follow-up and a usable sales process."
        root_cause = "No major conversion constraint detected from your answers."
        impact = "Paid revenue should track qualified demand without systematic leakage in follow-up or closing."
        expected = "Maintain documented stages and follow-up discipline as volume grows."
    else:
        finding = findings[0]["reasoning"]
        root_cause = "; ".join(f["reasoning"] for f in findings)
        impact = (
            "Revenue is lost after leads are already serious — marketing spend and selling time "
            "do not fully convert to cash."
        )
        expected = (
            "Higher close rate on existing serious leads, fewer deals dying in follow-up, "
            "and less founder time per closed deal."
        )

    formatted = (
        f"Finding:\n{finding}\n\n"
        f"Root Cause:\n{root_cause}\n\n"
        f"Business Impact:\n{impact}\n\n"
        f"Score: {score}/100 ({status})\n\n"
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
        "recommended_action": play["next_step"],
        "expected_outcome": expected,
        "formatted": formatted,
    }


def _rules_pricing(a: dict) -> list[dict]:
    out = []
    pc = a.get("pricing_confidence", "")
    if pc == "Probably underpriced":
        out.append({"penalty": 25, "evidence": [_ev(a, "pricing_confidence")],
                    "reasoning": "Self-admitted underpricing is the cheapest revenue fix that exists — no new leads required."})
    elif pc == "Honestly, no idea":
        out.append({"penalty": 20, "evidence": [_ev(a, "pricing_confidence")],
                    "reasoning": "Pricing has never been tested against willingness to pay; the current number is a guess carrying the whole P&L."})
    if a.get("last_price_change") == "Never":
        out.append({"penalty": 15, "evidence": [_ev(a, "last_price_change")],
                    "reasoning": "Prices have never changed while costs certainly have. Margin erodes silently every year."})
    if a.get("discounting") == "Most deals":
        out.append({"penalty": 20, "evidence": [_ev(a, "discounting")],
                    "reasoning": "Discounting on most deals means the list price isn't real — buyers have learned to wait for it."})
    return out


def _rules_retention(a: dict) -> list[dict]:
    out = []
    rr = _num(a, "repeat_rate")
    model = a.get("revenue_model", "")
    if rr is not None and rr < 30 and model in ("Recurring (retainers / subscriptions)", "Repeat transactional (orders)", "Mixed"):
        out.append({"penalty": 30, "evidence": [_ev(a, "repeat_rate"), _ev(a, "revenue_model")],
                    "reasoning": f"A ~{int(rr)}% repeat rate in a repeat-revenue model means the business refills a leaking bucket every month — growth spend is fighting churn."})
    if a.get("churn_reason_known") == "No":
        out.append({"penalty": 20, "evidence": [_ev(a, "churn_reason_known")],
                    "reasoning": "Nobody knows why customers leave, so retention can't be fixed — only guessed at."})
    if a.get("retention_process") == "None":
        out.append({"penalty": 15, "evidence": [_ev(a, "retention_process")],
                    "reasoning": "No deliberate reason for customers to come back; repeat revenue is being left to chance."})
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
    if a.get("documented_sales_process") == "No":
        out.append({"penalty": 15, "evidence": [_ev(a, "documented_sales_process")],
                    "reasoning": "An undocumented sales process can't be delegated, improved, or diagnosed — it can only be performed."})
    return out


_RULES = {
    "demand": _rules_demand,
    "qualification": _rules_qualification,
    "conversion": _rules_conversion,
    "pricing": _rules_pricing,
    "retention": _rules_retention,
    "founder_dependency": _rules_founder,
}

# Constraint -> next step + opportunity heuristic (uplift fraction of annual revenue, shown with formula)
_CONSTRAINT_PLAYBOOK = {
    "demand": {
        "next_step": "Before spending on ads: pick ONE additional lead source that matches how your customers already buy, and commit to it for 30 days. Volume is the cap right now — nothing downstream can compensate.",
        "uplift": 0.15,
    },
    "qualification": {
        "next_step": "Write down 3 disqualifying questions and ask them in the first conversation. The goal this month is fewer conversations, not more.",
        "uplift": 0.08,
    },
    "conversion": {
        "next_step": "Install a dead-simple follow-up system this week: every open lead gets a next-touch date, and no lead is closed-lost before 5 touches. This is the highest-leverage fix because the leads are already paid for.",
        "uplift": 0.20,
    },
    "pricing": {
        "next_step": "Quote 15–20% higher to the next three NEW prospects only. Existing customers unchanged. You are buying information about willingness to pay for the price of three conversations.",
        "uplift": 0.12,
    },
    "retention": {
        "next_step": "Call five customers who stopped buying and ask one question: 'what changed?' Do not sell on the call. Their answers are the retention strategy.",
        "uplift": 0.18,
    },
    "founder_dependency": {
        "next_step": "Record yourself on the next three sales calls, then write the one-page playbook of what actually happens. You can't delegate what isn't written down.",
        "uplift": 0.10,
    },
}


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
        if d.get("score") is not None and d["score"] >= 80 and d["confidence"] >= 0.5
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


def compute_health(answers: dict) -> dict:
    """Full diagnosis. Returns either sufficient=False with what's missing,
    or the health score + per-dimension findings, all evidence-cited."""
    dims_out = []
    total_conf_weight = 0.0
    weighted_score = 0.0

    for key, meta in DIMENSIONS.items():
        conf = _dimension_confidence(answers, key)
        missing = [_QLABEL[f] for f in meta["fields"] if answers.get(f) in (None, "")]
        findings = _RULES[key](answers) if conf > 0 else []
        score = None
        if conf >= 0.5:
            score = max(0, 100 - sum(f["penalty"] for f in findings))
            weighted_score += score * conf
            total_conf_weight += conf
        dims_out.append({
            "key": key,
            "label": meta["label"],
            "score": score,
            "confidence": conf,
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
            "missing_summary": [d["label"] for d in dims_out if d["confidence"] < 0.5],
        }

    health = round(weighted_score / total_conf_weight)
    scored = [d for d in dims_out if d["score"] is not None]
    primary = min(scored, key=lambda d: d["score"])
    overall_conf = round(total_conf_weight / len(DIMENSIONS), 2)

    risk = "Low Risk" if health >= 75 else ("Moderate Risk" if health >= 55 else "High Risk")

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
        },
        "revenue_opportunity": opportunity,
        "recommended_next_step": play["next_step"] if play else None,
        "dimensions": sorted(dims_out, key=lambda d: (d["score"] is None, d["score"] if d["score"] is not None else 0)),
        "missing_summary": [d["label"] for d in dims_out if d["confidence"] < 0.5],
        "method_note": ("Scores are rule-based and deterministic. Every dimension starts at 100; each finding "
                        "subtracts a stated penalty, and every finding cites the answers it is based on. "
                        "Confidence reflects how much of the audit is answered for that dimension."),
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


def compute_open_questions(answers: dict) -> list[str]:
    """Questions AFK still has: unanswered audit fields first (real gaps),
    then constraint-specific probes. Max 5."""
    h = compute_health(answers)
    out = []
    # Real evidence gaps, most-impactful dimensions first
    for d in h["dimensions"]:
        for m in d.get("missing", []):
            q = f"{m}?" if not m.endswith("?") else m
            if q not in out:
                out.append(q)
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
        "why": top["reasoning"] if top else "This dimension scored lowest among all measured dimensions.",
        "evidence": [e for f in pc["findings"] for e in f["evidence"]],
        "confidence_pct": int(pc["confidence"] * 100),
        "confidence_basis": f"Based on {int(pc['confidence'] * 100)}% audit coverage of {pc['label']} and deterministic scoring rules.",
        "assumptions": ("Assumes stated audit answers are accurate, and that the uplift heuristic "
                        f"({int(play.get('uplift', 0) * 100)}% of annual revenue) transfers to this business — "
                        "unvalidated until tested."),
        "expected_impact": "High" if play.get("uplift", 0) >= 0.15 else "Medium",
    }

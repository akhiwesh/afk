"""
Revenue Diagnostic Instrument — modular Business System blocks.

Each module groups questions by anatomy, maps to engine dimension(s),
and produces a deterministic micro-payoff after sufficient coverage.
"""
from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi

_MODULE_METRIC_KEYS = {
    "demand": ("lead_count", "lead_conversion_pct", "top_lead_source"),
    "qualification": ("lead_count",),
    "conversion": ("lead_conversion_pct",),
    "pricing": ("avg_discount_pct", "avg_order_value", "avg_monthly_revenue"),
    "retention": ("repeat_customer_rate",),
}

# Module order for the sectional wizard
AUDIT_MODULES = [
    {
        "id": "context",
        "title": "Business Context",
        "hook": "We establish what kind of business this is before testing how it earns.",
        "sections": ["profile", "revenue"],
        "dimensions": [],
        "evidence_hint": None,
        "min_coverage": 1.0,
        "diagnostic": False,
    },
    {
        "id": "reflection",
        "title": "Your Hypothesis",
        "hook": "We capture what you believe is wrong — before examining each system, so we can cross-examine later.",
        "sections": ["goals"],
        "dimensions": [],
        "evidence_hint": None,
        "min_coverage": 1.0,
        "diagnostic": False,
    },
    {
        "id": "demand",
        "title": "Demand System",
        "hook": "We test whether new business is reliable or accidental.",
        "sections": ["demand"],
        "dimensions": ["demand"],
        "evidence_hint": "Upload a lead or CRM export to confirm volume and sources — self-report alone caps confidence at 40%.",
        "min_coverage": 1.0,
        "diagnostic": True,
    },
    {
        "id": "qualification",
        "title": "Qualification System",
        "hook": "We test whether your calendar goes to the right leads.",
        "sections": ["qualification"],
        "dimensions": ["qualification"],
        "evidence_hint": "Lead statuses in a CRM export would measure how much time goes to wrong-fit leads.",
        "min_coverage": 1.0,
        "diagnostic": True,
    },
    {
        "id": "conversion",
        "title": "Conversion System",
        "hook": "We test how interest becomes revenue — follow-up and close discipline.",
        "sections": ["conversion"],
        "dimensions": ["conversion"],
        "evidence_hint": "Invoices plus lead outcomes would compute your real close rate.",
        "min_coverage": 1.0,
        "diagnostic": True,
    },
    {
        "id": "pricing",
        "title": "Pricing & Monetization",
        "hook": "We test whether you capture the value you create.",
        "sections": ["pricing"],
        "dimensions": ["pricing"],
        "evidence_hint": "Invoices with discount columns reveal real pricing behaviour — stronger than memory.",
        "min_coverage": 1.0,
        "diagnostic": True,
    },
    {
        "id": "retention",
        "title": "Retention System",
        "hook": "We test whether customers come back or the bucket leaks.",
        "sections": ["retention"],
        "dimensions": ["retention"],
        "evidence_hint": "12+ months of invoices measure true repeat rate.",
        "min_coverage": 1.0,
        "diagnostic": True,
    },
    {
        "id": "operations",
        "title": "Founder Dependency",
        "hook": "We test how much revenue depends on you personally.",
        "sections": ["operations"],
        "dimensions": ["founder_dependency"],
        "evidence_hint": "No uploadable evidence verifies this yet — call and meeting data arrives later.",
        "min_coverage": 1.0,
        "diagnostic": True,
    },
]

_MODULE_BY_ID = {m["id"]: m for m in AUDIT_MODULES}


def get_module(module_id: str) -> dict | None:
    return _MODULE_BY_ID.get(module_id)

_QUESTIONS_BY_SECTION: dict[str, list[dict]] = {}
for q in ce.QUESTIONS:
    _QUESTIONS_BY_SECTION.setdefault(q["section"], []).append(q)

_OPTIONAL_BY_SECTION: dict[str, list[dict]] = {}
for q in ce.OPTIONAL_QUESTIONS:
    _OPTIONAL_BY_SECTION.setdefault(q["section"], []).append(q)


def module_required_question_ids(module: dict) -> list[str]:
    ids = []
    for sec in module["sections"]:
        for q in _QUESTIONS_BY_SECTION.get(sec, []):
            ids.append(q["id"])
    return ids


def module_optional_questions(module: dict) -> list[dict]:
    out = []
    for sec in module["sections"]:
        out.extend(_OPTIONAL_BY_SECTION.get(sec, []))
    return out


def module_question_ids(module: dict) -> list[str]:
    """Required question ids — drives module completion progress."""
    return module_required_question_ids(module)


def module_save_question_ids(module: dict) -> list[str]:
    """Required + optional ids accepted on module save."""
    return module_required_question_ids(module) + [q["id"] for q in module_optional_questions(module)]


def module_questions(module: dict) -> list[dict]:
    out = []
    for sec in module["sections"]:
        out.extend(_QUESTIONS_BY_SECTION.get(sec, []))
    for q in module_optional_questions(module):
        out.append({**q, "optional": True})
    return out


def module_progress(module: dict, answers: dict) -> dict:
    qids = module_question_ids(module)
    answered = sum(1 for qid in qids if answers.get(qid) not in (None, ""))
    total = len(qids)
    coverage = round(answered / total, 2) if total else 0.0
    return {
        "answered": answered,
        "total": total,
        "coverage": coverage,
        "complete": coverage >= module.get("min_coverage", 1.0) and answered > 0,
    }


def _status_label(score: int | None, confidence: float, module_id: str | None = None) -> str:
    if score is None or not ce._dimension_scorable(confidence):
        return "insufficient"
    label = ce.system_status(score)
    return {
        "Stable": "healthy",
        "Watch": "pressure",
        "Constrained": "pressure",
        "Critical": "constraint",
    }.get(label, "insufficient")


def _headline(module: dict, dim: dict | None, progress: dict) -> str:
    if not module.get("diagnostic"):
        if module["id"] == "context":
            bt = None  # filled by caller via answers
            return "Context captured — we can now examine each revenue system."
        if module["id"] == "reflection":
            return "Your hypothesis is recorded — we'll compare it to measured evidence."
    if not progress["complete"]:
        missing = progress["total"] - progress["answered"]
        return f"Answer {missing} more question{'s' if missing != 1 else ''} in this system to see findings."
    if dim is None or dim.get("score") is None:
        return "Not enough answers in this system yet to score it."
    findings = dim.get("findings", [])
    if not findings:
        return f"{dim['label']} looks healthy from what you've told us so far."
    top = findings[0]
    return top["reasoning"]


def compute_module_payoff(
    module_id: str,
    answers: dict,
    evidence_metrics: dict | None = None,
) -> dict:
    """Deterministic micro-diagnosis for one Business System block."""
    module = _MODULE_BY_ID.get(module_id)
    if not module:
        raise ValueError(f"Unknown audit module: {module_id}")

    progress = module_progress(module, answers)
    payoff = {
        "module_id": module_id,
        "title": module["title"],
        "hook": module["hook"],
        "progress": progress,
        "ready": progress["complete"],
        "evidence_hint": module.get("evidence_hint"),
        "diagnostic": module.get("diagnostic", True),
    }

    if not progress["complete"]:
        qids = module_question_ids(module)
        missing_labels = [
            ce._QLABEL.get(qid, qid)
            for qid in qids
            if answers.get(qid) in (None, "")
        ]
        payoff["headline"] = _headline(module, None, progress)
        payoff["missing"] = missing_labels[:5]
        payoff["status"] = "incomplete"
        return payoff

    if not module.get("diagnostic"):
        if module["id"] == "context":
            bt = answers.get("business_type") or "your business"
            payoff["headline"] = f"Context set for {bt.split(' / ')[0] if bt else 'this business'} — examining revenue systems next."
            payoff["status"] = "captured"
            payoff["summary"] = {
                "business_type": answers.get("business_type"),
                "revenue_model": answers.get("revenue_model"),
                "growth_stage": answers.get("growth_stage"),
            }
        else:
            payoff["headline"] = _headline(module, None, progress)
            payoff["status"] = "captured"
            if answers.get("self_diagnosis"):
                payoff["summary"] = {"self_diagnosis": answers.get("self_diagnosis")}
        return payoff

    health = ce.compute_health(answers)
    dim_key = module["dimensions"][0]
    dim = next((d for d in health.get("dimensions", []) if d["key"] == dim_key), None)

    if dim is None:
        payoff["headline"] = "Could not evaluate this system."
        payoff["status"] = "insufficient"
        return payoff

    score = dim.get("score")
    coverage = dim.get("coverage", dim.get("confidence", 0))
    epi_conf = dim.get("confidence", 0)
    status = _status_label(score, coverage, module_id)

    payoff["dimension"] = {
        "key": dim["key"],
        "label": dim["label"],
        "score": score,
        "coverage": coverage,
        "confidence": epi_conf,
    }
    payoff["findings"] = dim.get("findings", [])
    payoff["missing_fields"] = dim.get("missing", [])
    payoff["status"] = status
    payoff["headline"] = _headline(module, dim, progress)

    if score is not None and module.get("diagnostic"):
        if module_id == "conversion":
            system_finding = ce.build_conversion_system_finding(answers)
        else:
            dim_key = module["dimensions"][0]
            system_finding = ce.build_system_finding(dim_key, answers)
        payoff["system_finding"] = system_finding
        payoff["headline"] = system_finding["finding"]
        payoff["verdict"] = f"{dim['label']}: {system_finding['status'].lower()} ({score}/100)."
    elif status == "healthy":
        payoff["verdict"] = f"{dim['label']}: no major pressure detected from your answers."
    elif status == "insufficient":
        payoff["verdict"] = f"{dim['label']}: need more answers to score this system."
    elif status == "pressure":
        payoff["verdict"] = f"{dim['label']}: moderate pressure ({score}/100)."
    else:
        payoff["verdict"] = f"{dim['label']}: likely constraint ({score}/100)."

    if module.get("evidence_hint"):
        payoff["confidence_note"] = (
            f"Epistemic confidence for this system: {int(epi_conf * 100)}% (AFK-CFM-0001). "
            f"{module['evidence_hint']}"
        )

    play = ce._CONSTRAINT_PLAYBOOK.get(dim_key)
    if play and status == "constraint":
        payoff["micro_action"] = play.get("next_step")

    if evidence_metrics:
        keys = _MODULE_METRIC_KEYS.get(module_id, ())
        all_contra = evi.detect_contradictions(answers, evidence_metrics)
        relevant = [
            c for c in all_contra
            if c["evidence"]["metric"] in keys or module_id in ("pricing", "retention", "conversion")
        ][:2]
        if relevant:
            payoff["contradictions"] = relevant

    return payoff


def list_modules_state(answers: dict, evidence_metrics: dict | None = None) -> dict:
    """Full modular audit state for the wizard UI."""
    modules_out = []
    first_incomplete = None
    complete_count = 0

    for i, module in enumerate(AUDIT_MODULES):
        progress = module_progress(module, answers)
        item = {
            "id": module["id"],
            "title": module["title"],
            "hook": module["hook"],
            "order": i + 1,
            "diagnostic": module.get("diagnostic", True),
            "evidence_hint": module.get("evidence_hint"),
            "dimensions": module.get("dimensions", []),
            "progress": progress,
            "questions": module_questions(module),
        }
        if progress["complete"]:
            complete_count += 1
            item["payoff"] = compute_module_payoff(module["id"], answers, evidence_metrics)
        else:
            if first_incomplete is None:
                first_incomplete = module["id"]
        modules_out.append(item)

    state = {
        "modules": modules_out,
        "systems_complete": complete_count,
        "systems_total": len(AUDIT_MODULES),
        "current_module": first_incomplete or AUDIT_MODULES[-1]["id"],
        "sections": ce.AUDIT_SECTIONS,
    }
    if complete_count == len(AUDIT_MODULES):
        health = ce.compute_health(answers)
        if health.get("sufficient"):
            pc = health["primary_constraint"]
            state["diagnosis_preview"] = {
                "health_score": health["health_score"],
                "primary_constraint": pc["label"],
                "primary_score": pc["score"],
                "hypothesis_verdict": health.get("hypothesis_verdict"),
                "funnel_coherence": health.get("funnel_coherence"),
                "priority_model": ce.PRIORITY_MODEL_ID,
                "priority_ranking": (health.get("constraint_priority_ranking") or [])[:3],
                "compound_findings": (health.get("compound_findings") or [])[:2],
            }
    return state
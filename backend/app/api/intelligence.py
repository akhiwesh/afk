"""
Revenue Intelligence API — audit intake, business twin, executive diagnosis,
and The Analyst (one AI, evidence-grounded, never fakes certainty).
"""
import json
import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.core.database import get_session
from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi
from backend.app.core import audit_modules as am
from backend.app.bse.adapters.product import record_diagnosis_run, run_for_org
from backend.app.core.diagnostic_export import build_diagnostic_pdf, export_filename
from backend.app.core.twin_longitudinal import analyze_trajectory
from backend.app.bse.projection import diagnosis_memory_payload
from backend.app.models.intelligence import (
    RevenueAudit, DiagnosisSnapshot, EvidenceDataset, EvidenceRecord,
    BenchmarkSample, TreatmentOutcome, MemoryEvent,
)
from backend.app.knowledge_engine.outcome_tracking import (
    record_outcome, list_outcomes, outcome_to_dict, summarize_outcomes, OUTCOME_PROTOCOL_ID,
)
from backend.app.models.auth import User, Organization
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class AuditSave(BaseModel):
    answers: dict


class AnalystQuestion(BaseModel):
    question: str


class OutcomeRecord(BaseModel):
    constraint_key: str
    status: str  # started | completed | abandoned
    notes: str | None = None


def remember(db: Session, org_id: int, event_type: str, summary: str, payload: dict = None):
    """Append to Business Memory. Never raises into the caller's flow."""
    try:
        db.add(MemoryEvent(organization_id=org_id, event_type=event_type,
                           summary=summary, payload_json=json.dumps(payload or {})))
        db.commit()
    except Exception:
        db.rollback()


def _evidence_bundle(db: Session, org_id: int) -> dict:
    """Confirmed datasets -> records grouped by kind, quality by kind, row counts."""
    datasets = db.exec(select(EvidenceDataset).where(
        EvidenceDataset.organization_id == org_id,
        EvidenceDataset.status == "confirmed")).all()
    by_kind, quality, counts, sources = {}, {}, {}, []
    for d in datasets:
        recs = db.exec(select(EvidenceRecord).where(EvidenceRecord.dataset_id == d.id)).all()
        rows = [json.loads(r.data_json) for r in recs]
        by_kind.setdefault(d.dataset_type, []).extend(rows)
        counts[d.dataset_type] = counts.get(d.dataset_type, 0) + len(rows)
        try:
            q = json.loads(d.raw_json).get("quality")
        except Exception:
            q = None
        if q:
            prev = quality.get(d.dataset_type)
            quality[d.dataset_type] = q["score"] if prev is None else min(prev, q["score"])
        sources.append({"source": d.filename, "kind": d.dataset_type,
                        "detail": f"{d.row_count} rows",
                        "quality_pct": round((q["score"] if q else 0.8) * 100),
                        "quality_reasons": (q or {}).get("reasons", [])})
    return {"records_by_kind": by_kind, "quality_by_kind": quality,
            "kind_counts": counts, "sources": sources}


def _get_answers(db: Session, org_id: int) -> dict:
    audit = db.exec(select(RevenueAudit).where(RevenueAudit.organization_id == org_id)).first()
    if not audit:
        return {}
    try:
        return json.loads(audit.answers_json)
    except json.JSONDecodeError:
        return {}


def _attach_snapshot_changes(db: Session, org_id: int, health: dict) -> dict:
    """DB-only delta: what changed between the two most recent diagnosis snapshots."""
    snaps = db.exec(
        select(DiagnosisSnapshot)
        .where(DiagnosisSnapshot.organization_id == org_id)
        .order_by(DiagnosisSnapshot.created_at.desc())
        .limit(2)
    ).all()
    changes = None
    if len(snaps) == 2:
        latest, prev = snaps[0], snaps[1]
        cur = json.loads(latest.dimensions_json)
        old = json.loads(prev.dimensions_json)
        labels = {k: v["label"] for k, v in ce.DIMENSIONS.items()}
        improved, declined = [], []
        for k in set(cur) & set(old):
            delta = cur[k] - old[k]
            if delta > 0:
                improved.append({"dimension": labels.get(k, k), "delta": delta})
            elif delta < 0:
                declined.append({"dimension": labels.get(k, k), "delta": delta})
        changes = {
            "score_delta": latest.health_score - prev.health_score,
            "previous_score": prev.health_score,
            "previous_at": prev.created_at.isoformat(),
            "improved": sorted(improved, key=lambda x: -x["delta"]),
            "declined": sorted(declined, key=lambda x: x["delta"]),
            "constraint_changed": latest.primary_constraint != prev.primary_constraint,
            "previous_constraint": prev.primary_constraint,
        }
    health["changes"] = changes
    return health


@router.get("/onboarding")
def get_onboarding(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Revenue clarity checklist — evidence-first path for new founders."""
    org_id = current_user.organization_id
    answers = _get_answers(db, org_id)
    answered = sum(1 for q in ce.QUESTIONS if answers.get(q["id"]) not in (None, ""))
    total = len(ce.QUESTIONS)
    datasets = db.exec(
        select(EvidenceDataset).where(EvidenceDataset.organization_id == org_id)
    ).all()
    confirmed = [d for d in datasets if d.status == "confirmed"]
    health = ce.compute_health(answers)
    bundle = _evidence_bundle(db, org_id)
    return {
        "steps": [
            {
                "id": "audit",
                "label": "Revenue Audit",
                "done": answered >= total,
                "progress": answered,
                "total": total,
                "href": "#audit",
            },
            {
                "id": "evidence",
                "label": "Upload evidence",
                "done": len(confirmed) > 0,
                "progress": len(confirmed),
                "total": max(1, len(confirmed) or 1),
                "hint": "Invoices and CRM exports",
                "href": "#evidence",
            },
            {
                "id": "diagnosis",
                "label": "Revenue clarity",
                "done": health.get("sufficient", False) and len(confirmed) > 0,
                "progress": 1 if health.get("sufficient") else 0,
                "total": 1,
                "href": "#diagnosis",
            },
        ],
        "audit_complete": answered >= total,
        "evidence_count": len(confirmed),
        "diagnosis_ready": health.get("sufficient", False),
        "has_evidence_metrics": bool(bundle["kind_counts"]),
    }


def _merge_audit_answers(db: Session, org_id: int, raw: dict) -> dict:
    clean = {k: v for k, v in raw.items() if k in ce.QUESTION_IDS}
    if len(clean) != len(raw):
        unknown = set(raw) - ce.QUESTION_IDS
        raise HTTPException(status_code=422, detail=f"Unknown question ids: {sorted(unknown)}")

    audit = db.exec(select(RevenueAudit).where(
        RevenueAudit.organization_id == org_id)).first()
    if not audit:
        audit = RevenueAudit(organization_id=org_id, answers_json="{}")

    merged = {**json.loads(audit.answers_json or "{}"), **clean}
    merged = {k: v for k, v in merged.items() if v not in (None, "")}
    audit.answers_json = json.dumps(merged)
    audit.updated_at = datetime.now(timezone.utc)
    db.add(audit)
    db.commit()
    return merged


def _finalize_audit_diagnosis(db: Session, org_id: int, merged: dict) -> dict:
    """Run full pipeline after audit save; return health summary."""
    org = db.get(Organization, org_id)
    pipeline = run_for_org(db, org_id, org.name if org else None)
    health = pipeline.clarity
    record_diagnosis_run(db, org_id, pipeline)

    if health.get("sufficient"):
        rev = merged.get("monthly_revenue")
        band = None
        if isinstance(rev, (int, float)) and rev > 0:
            edges = [(200000, "<2L"), (500000, "2L-5L"), (1000000, "5L-10L"),
                     (2500000, "10L-25L"), (10000000, "25L-1Cr")]
            band = next((b for lim, b in edges if rev < lim), "1Cr+")
        db.add(BenchmarkSample(
            business_type=merged.get("business_type"),
            industry=merged.get("industry"),
            growth_stage=merged.get("growth_stage"),
            team_size=int(merged["team_size"]) if str(merged.get("team_size", "")).isdigit() else None,
            revenue_band=band,
            metrics_json=json.dumps({
                "conversion_close_rate": merged.get("conversion_close_rate"),
                "repeat_rate": merged.get("repeat_rate"),
                "leads_per_month": merged.get("leads_per_month"),
                "health_score": health["health_score"],
            }),
        ))
        db.commit()

    answered = sum(1 for q in ce.QUESTIONS if merged.get(q["id"]) not in (None, ""))
    remember(db, org_id, "audit_saved",
             f"Revenue Audit updated — {answered}/{len(ce.QUESTIONS)} answered.",
             {"answered": answered})
    if health.get("sufficient"):
        primary = health["primary_constraint"]["label"]
        remember(db, org_id, "diagnosis_run",
                 f"Diagnosis computed: Revenue Health {health['health_score']}/100, "
                 f"primary constraint {primary}.",
                 diagnosis_memory_payload(pipeline))
    return health


@router.get("/audit/questions")
def get_questions(current_user: User = Depends(get_current_user)):
    return {
        "sections": ce.AUDIT_SECTIONS,
        "questions": ce.QUESTIONS,
        "optional_questions": ce.OPTIONAL_QUESTIONS,
        "question_metadata": ce.QUESTION_METADATA,
        "audit_spec_id": "AFK-AUD-0001",
    }


@router.get("/audit/modules")
def get_audit_modules(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Sectional audit wizard — Business System blocks with per-module progress."""
    org_id = current_user.organization_id
    answers = _get_answers(db, org_id)
    bundle = _evidence_bundle(db, org_id)
    metrics = evi.compute_metrics(bundle["records_by_kind"]) if bundle["kind_counts"] else None
    state = am.list_modules_state(answers, metrics)
    state["answers"] = answers
    state["answered"] = sum(1 for q in ce.QUESTIONS if answers.get(q["id"]) not in (None, ""))
    state["total"] = len(ce.QUESTIONS)
    return state


@router.get("/audit/modules/{module_id}")
def get_audit_module(
    module_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    module = am.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Unknown audit module")
    org_id = current_user.organization_id
    answers = _get_answers(db, org_id)
    bundle = _evidence_bundle(db, org_id)
    metrics = evi.compute_metrics(bundle["records_by_kind"]) if bundle["kind_counts"] else None
    progress = am.module_progress(module, answers)
    payoff = am.compute_module_payoff(module_id, answers, metrics) if progress["complete"] else None
    return {
        "module": {
            "id": module_id,
            "title": module["title"],
            "hook": module["hook"],
            "questions": am.module_questions(module),
            "evidence_hint": module.get("evidence_hint"),
            "progress": progress,
        },
        "answers": {q["id"]: answers.get(q["id"]) for q in am.module_questions(module)},
        "payoff": payoff,
    }


@router.put("/audit/modules/{module_id}")
def save_audit_module(
    module_id: str,
    data: AuditSave,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Save one Business System block and return immediate micro-payoff."""
    module = am.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Unknown audit module")
    allowed = set(am.module_save_question_ids(module))
    submitted = set(data.answers)
    bad = submitted - allowed
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"Questions {sorted(bad)} do not belong to module '{module_id}'",
        )

    org_id = current_user.organization_id
    merged = _merge_audit_answers(db, org_id, data.answers)
    bundle = _evidence_bundle(db, org_id)
    metrics = evi.compute_metrics(bundle["records_by_kind"]) if bundle["kind_counts"] else None
    progress = am.module_progress(module, merged)
    payoff = am.compute_module_payoff(module_id, merged, metrics)

    remember(db, org_id, "audit_module_saved",
             f"{module['title']} examined — {progress['answered']}/{progress['total']} answered.",
             {"module_id": module_id, "progress": progress, "status": payoff.get("status")})

    health = None
    diagnosed = False
    if progress["complete"] and module.get("diagnostic"):
        org = db.get(Organization, org_id)
        pipeline = run_for_org(db, org_id, org.name if org else None)
        health = pipeline.clarity
        if health.get("sufficient"):
            record_diagnosis_run(db, org_id, pipeline)

    modules_state = am.list_modules_state(merged, metrics)
    mod_list = modules_state["modules"]
    idx = next(i for i, m in enumerate(mod_list) if m["id"] == module_id)
    next_module = mod_list[idx + 1]["id"] if idx + 1 < len(mod_list) else None
    all_complete = modules_state["systems_complete"] == modules_state["systems_total"]

    if all_complete:
        health = _finalize_audit_diagnosis(db, org_id, merged)
        diagnosed = bool(health.get("sufficient"))

    return {
        "saved": True,
        "module_id": module_id,
        "progress": progress,
        "payoff": payoff,
        "next_module": next_module,
        "all_modules_complete": all_complete,
        "systems_complete": modules_state["systems_complete"],
        "systems_total": modules_state["systems_total"],
        "diagnosed": diagnosed,
        "health_preview": {
            "sufficient": health.get("sufficient") if health else False,
            "health_score": health.get("health_score") if health else None,
            "primary_constraint": (health.get("primary_constraint") or {}).get("label") if health else None,
        } if health else None,
    }


@router.get("/audit")
def get_audit(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    answers = _get_answers(db, current_user.organization_id)
    answered = sum(1 for q in ce.QUESTIONS if answers.get(q["id"]) not in (None, ""))
    return {"answers": answers, "answered": answered, "total": len(ce.QUESTIONS)}


@router.put("/audit")
def save_audit(
    data: AuditSave,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    merged = _merge_audit_answers(db, org_id, data.answers)
    health = _finalize_audit_diagnosis(db, org_id, merged)
    answered = sum(1 for q in ce.QUESTIONS if merged.get(q["id"]) not in (None, ""))
    return {"saved": True, "answered": answered, "total": len(ce.QUESTIONS),
            "diagnosed": health.get("sufficient", False)}


@router.get("/twin")
def get_twin(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    org = db.get(Organization, current_user.organization_id)
    output = run_for_org(db, current_user.organization_id, org.name if org else None)
    return output.twin


@router.get("/trajectory")
def get_trajectory(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Longitudinal diagnosis analysis from DiagnosisSnapshot history."""
    org_id = current_user.organization_id
    snaps = db.exec(
        select(DiagnosisSnapshot)
        .where(DiagnosisSnapshot.organization_id == org_id)
        .order_by(DiagnosisSnapshot.created_at.desc())
        .limit(24)
    ).all()
    trajectory = analyze_trajectory(snaps)
    outcomes = list_outcomes(db, org_id)
    trajectory["outcome_tracking"] = summarize_outcomes(outcomes)
    trajectory["recent_outcomes"] = [outcome_to_dict(o) for o in outcomes[:5]]
    return trajectory


@router.get("/outcomes")
def get_outcomes(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """AFK-OUT-0001 treatment outcome records for this organization."""
    org_id = current_user.organization_id
    rows = list_outcomes(db, org_id)
    return {
        "protocol_id": OUTCOME_PROTOCOL_ID,
        "summary": summarize_outcomes(rows),
        "outcomes": [outcome_to_dict(r) for r in rows],
    }


@router.post("/outcomes")
def post_outcome(
    data: OutcomeRecord,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Record treatment started/completed/abandoned — links to diagnosis baseline."""
    org_id = current_user.organization_id
    if data.constraint_key not in ce.DIMENSIONS:
        raise HTTPException(status_code=422, detail=f"Unknown constraint: {data.constraint_key}")
    if data.status not in ("started", "completed", "abandoned"):
        raise HTTPException(status_code=422, detail="status must be started, completed, or abandoned")

    org = db.get(Organization, org_id)
    output = run_for_org(db, org_id, org.name if org else None)
    health = output.clarity
    if not health.get("sufficient"):
        raise HTTPException(status_code=400, detail="Complete the Revenue Audit before recording treatment outcomes.")

    try:
        row = record_outcome(db, org_id, data.constraint_key, data.status, health, data.notes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    label = ce.DIMENSIONS[data.constraint_key]["label"]
    remember(db, org_id, "treatment_outcome",
             f"Treatment {data.status} for {label} — verdict {row.outcome_verdict}.",
             {"constraint_key": data.constraint_key, "status": data.status,
              "outcome_verdict": row.outcome_verdict, "protocol_id": OUTCOME_PROTOCOL_ID})

    return {"saved": True, "outcome": outcome_to_dict(row)}


@router.get("/health")
def get_health(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    org = db.get(Organization, current_user.organization_id)
    output = run_for_org(db, current_user.organization_id, org.name if org else None)
    health = dict(output.clarity)
    return _attach_snapshot_changes(db, current_user.organization_id, health)


@router.get("/health/export.pdf")
def export_health_pdf(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Download executive diagnosis as a shareable PDF memo."""
    org = db.get(Organization, current_user.organization_id)
    org_name = org.name if org else None
    output = run_for_org(db, current_user.organization_id, org_name)
    health = _attach_snapshot_changes(db, current_user.organization_id, dict(output.clarity))
    try:
        pdf_bytes = build_diagnostic_pdf(health, org_name=org_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = export_filename(org_name)
    remember(db, current_user.organization_id, "diagnosis_exported",
             f"Executive diagnosis PDF exported ({filename}).",
             {"filename": filename, "health_score": health.get("health_score")})

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/memory/timeline")
def get_timeline(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Business Memory, chronological. Append-only record of everything AFK
    has learned about this business."""
    events = db.exec(select(MemoryEvent)
                     .where(MemoryEvent.organization_id == current_user.organization_id)
                     .order_by(MemoryEvent.occurred_at.desc()).limit(200)).all()
    return [{"type": e.event_type, "at": e.occurred_at.isoformat(),
             "summary": e.summary, "detail": json.loads(e.payload_json)} for e in events]


# ---------------------------------------------------------------------------
# The Analyst — one AI. Evidence-grounded. Two honest modes:
#   * LLM mode when an API key is configured (ANTHROPIC_API_KEY or GEMINI_API_KEY)
#   * Deterministic mode otherwise: real computed findings, clearly labeled.
# ---------------------------------------------------------------------------

_ANALYST_SYSTEM = (
    "You are The Analyst at AFK, a Revenue Intelligence company. You help founders understand "
    "why revenue isn't growing before telling them how to grow it. You reason like an elite, "
    "calm strategy consultant — direct, evidence-first, no hype.\n\n"
    "HARD RULES:\n"
    "- Ground every claim in the business evidence provided. If evidence doesn't support an answer, say so.\n"
    "- Never invent numbers. Never state certainty you don't have.\n"
    "- Structure EVERY reply in exactly these sections, using these headings:\n"
    "What I believe:\nWhy I believe it:\nConfidence:\nMissing information:\nSuggested next question:\n"
    "- Confidence is one of: Low / Moderate / High, with one sentence of justification.\n"
    "- Keep the whole reply under 250 words."
)


def _pipeline_context(output) -> str:
    ctx = {
        "business_twin": output.twin,
        "diagnosis": output.clarity,
        "provenance": output.provenance.as_dict(),
    }
    clarity = output.clarity
    if clarity.get("evidence_metrics"):
        ctx["evidence_metrics"] = clarity["evidence_metrics"]
    if clarity.get("contradictions"):
        ctx["contradictions"] = clarity["contradictions"]
    if clarity.get("evidence_sources"):
        ctx["data_sources"] = clarity["evidence_sources"]
    return json.dumps(ctx, default=str)


def _deterministic_analysis(question: str, answers: dict, contradictions: list = None) -> str:
    health = ce.compute_health(answers)
    if not health.get("sufficient"):
        missing = ", ".join(health.get("missing_summary", [])) or "most of the audit"
        return (
            "What I believe:\nThere is not enough evidence yet to diagnose this business. I will not guess.\n\n"
            "Why I believe it:\nThe Revenue Audit is only "
            f"{int(health.get('completeness', 0) * 100)}% complete; the weakest-covered areas are: {missing}.\n\n"
            "Confidence:\nHigh — this is a statement about missing data, not about the business.\n\n"
            "Missing information:\nComplete the audit sections listed above.\n\n"
            "Suggested next question:\nOpen the Revenue Audit and answer the sections above — "
            "then ask me this again.\n\n"
            "— Deterministic mode: this response was computed by the constraint engine. "
            "Add an AI API key for conversational analysis."
        )

    pc = health["primary_constraint"]
    findings = pc.get("findings", [])
    reasons = "\n".join(f"- {f['reasoning']}" for f in findings) or "- Dimension scored lowest among all measured dimensions."
    evidence_bits = []
    for f in findings:
        for e in f.get("evidence", []):
            evidence_bits.append(f"{e['question']}: \"{e['answer']}\"")
    evidence_txt = "; ".join(dict.fromkeys(evidence_bits)) or "audit answers"
    conf_word = "High" if pc["confidence"] >= 0.75 else ("Moderate" if pc["confidence"] >= 0.5 else "Low")
    missing = ", ".join(health.get("missing_summary", [])) or "None significant — audit coverage is good."
    contra_note = ""
    if contradictions:
        c = contradictions[0]
        contra_note = ("\n\nNote — evidence contradicts a stated belief: "
                       f"you answered \"{c['belief']['answer']}\" for {c['belief']['question']}, "
                       f"but {c['evidence']['basis']} shows {c['evidence']['value']}. "
                       f"{c['follow_up_question']}")

    return (
        f"What I believe:\nThe primary constraint on revenue right now is {pc['label']} "
        f"(dimension score {pc['score']}/100; overall Revenue Health {health['health_score']}/100, {health['risk_level']}).\n\n"
        f"Why I believe it:\n{reasons}\nEvidence cited: {evidence_txt}.\n\n"
        f"Confidence:\n{conf_word} — based on {int(pc['confidence'] * 100)}% audit coverage of this dimension and deterministic rules.\n\n"
        f"Missing information:\n{missing}\n\n"
        f"Suggested next question:\nAsk me: \"What exactly should I do about {pc['label'].lower()} this week?\" "
        f"(Current recommendation: {health.get('recommended_next_step', 'complete more of the audit.')})\n\n"
        + contra_note +
        "\n\n— Deterministic mode: this response was computed by the constraint engine, not generated by an LLM. "
        "Add an AI API key for conversational analysis."
    )


def _call_anthropic(key: str, question: str, evidence: str) -> str:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 700,
            "system": _ANALYST_SYSTEM,
            "messages": [{"role": "user", "content": f"BUSINESS EVIDENCE (JSON):\n{evidence}\n\nFOUNDER'S QUESTION:\n{question}"}],
        },
        timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def _call_gemini(key: str, question: str, evidence: str) -> str:
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": f"{_ANALYST_SYSTEM}\n\nBUSINESS EVIDENCE (JSON):\n{evidence}\n\nFOUNDER'S QUESTION:\n{question}"}]}]},
        timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


@router.post("/analyst")
def ask_analyst(
    q: AnalystQuestion,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    question = q.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty")
    if len(question) > 2000:
        raise HTTPException(status_code=422, detail="Question too long (2000 char max)")

    org = db.get(Organization, current_user.organization_id)
    output = run_for_org(db, current_user.organization_id, org.name if org else None)
    answers = _get_answers(db, current_user.organization_id)
    evidence = _pipeline_context(output)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    mode = "deterministic"
    try:
        if anthropic_key:
            text, mode = _call_anthropic(anthropic_key, question, evidence), "llm"
        elif gemini_key:
            text, mode = _call_gemini(gemini_key, question, evidence), "llm"
        else:
            text = _deterministic_analysis(
                question, answers, output.clarity.get("contradictions"))
    except Exception:
        text = ("(The AI provider could not be reached — showing the constraint engine's computed "
                "analysis instead.)\n\n" + _deterministic_analysis(
                    question, answers, output.clarity.get("contradictions")))
        mode = "deterministic_fallback"

    return {"answer": text, "mode": mode}

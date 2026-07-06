"""Product-layer adapters: DB evidence bundle → BSE contracts."""
import json

from sqlmodel import Session, select

from backend.app.bse.contracts.diagnosis import PipelineOutput
from backend.app.bse.contracts.evidence import EvidenceBundle, PipelineInput
from backend.app.bse.orchestrator import DiagnosticPipeline
from backend.app.bse.projection import diagnosis_memory_payload, persist_diagnosis_snapshot
from backend.app.models.intelligence import EvidenceDataset, EvidenceRecord, RevenueAudit


def evidence_bundle_from_raw(raw: dict) -> EvidenceBundle:
    """Convert the legacy _evidence_bundle dict into an EvidenceBundle."""
    return EvidenceBundle(
        records_by_kind=raw.get("records_by_kind", {}),
        kind_counts=raw.get("kind_counts", {}),
        quality_by_kind=raw.get("quality_by_kind", {}),
        sources=tuple(raw.get("sources", [])),
    )


def load_evidence_bundle(db: Session, org_id: int) -> EvidenceBundle:
    """Load confirmed datasets for an org into an EvidenceBundle."""
    datasets = db.exec(
        select(EvidenceDataset).where(
            EvidenceDataset.organization_id == org_id,
            EvidenceDataset.status == "confirmed",
        )
    ).all()
    by_kind: dict[str, list[dict]] = {}
    quality: dict[str, float] = {}
    counts: dict[str, int] = {}
    sources: list[dict] = []

    for d in datasets:
        recs = db.exec(
            select(EvidenceRecord).where(EvidenceRecord.dataset_id == d.id)
        ).all()
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
        sources.append({
            "source": d.filename,
            "kind": d.dataset_type,
            "detail": f"{d.row_count} rows",
            "quality_pct": round((q["score"] if q else 0.8) * 100),
            "quality_reasons": (q or {}).get("reasons", []),
        })

    return EvidenceBundle(
        records_by_kind=by_kind,
        kind_counts=counts,
        quality_by_kind=quality,
        sources=tuple(sources),
    )


def load_audit_answers(db: Session, org_id: int) -> dict:
    audit = db.exec(
        select(RevenueAudit).where(RevenueAudit.organization_id == org_id)
    ).first()
    if not audit:
        return {}
    try:
        return json.loads(audit.answers_json)
    except json.JSONDecodeError:
        return {}


def pipeline_input_from_org(
    db: Session,
    org_id: int,
    org_name: str | None = None,
    kb_release: str = "legacy-hardcoded",
) -> PipelineInput:
    return PipelineInput(
        audit_answers=load_audit_answers(db, org_id),
        evidence=load_evidence_bundle(db, org_id),
        org_name=org_name,
        kb_release=kb_release,
    )


def run_for_org(db: Session, org_id: int, org_name: str | None = None) -> PipelineOutput:
    inputs = pipeline_input_from_org(db, org_id, org_name=org_name)
    return DiagnosticPipeline.run(inputs)


def record_diagnosis_run(db: Session, org_id: int, output: PipelineOutput) -> bool:
    """Persist snapshot + return whether a sufficient diagnosis was recorded."""
    return persist_diagnosis_snapshot(db, org_id, output)
"""Treatment outcome tracking — AFK-OUT-0001."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from backend.app.core import engine as ce
from backend.app.models.intelligence import DiagnosisSnapshot, TreatmentOutcome

OUTCOME_PROTOCOL_ID = "AFK-OUT-0001"

_CONSTRAINT_TO_TRT = {
    key: f"AFK-TRT-{i:04d}"
    for i, key in enumerate(ce._CONSTRAINT_PLAYBOOK.keys(), start=1)
}

_VALID_STATUS = frozenset({"started", "completed", "abandoned"})


def _latest_snapshot(db: Session, org_id: int) -> DiagnosisSnapshot | None:
    return db.exec(
        select(DiagnosisSnapshot)
        .where(DiagnosisSnapshot.organization_id == org_id)
        .order_by(DiagnosisSnapshot.created_at.desc())
    ).first()


def _dimension_score_from_health(health: dict, constraint_key: str) -> int | None:
    for d in health.get("dimensions", []):
        if d.get("key") == constraint_key:
            return d.get("score")
    return None


def _verdict(baseline: int | None, followup: int | None, snap_count: int) -> str:
    if baseline is None or followup is None or snap_count < 1:
        return "insufficient_data"
    if followup > baseline:
        return "improved"
    if followup < baseline:
        return "declined"
    return "unchanged"


def record_outcome(
    db: Session,
    org_id: int,
    constraint_key: str,
    status: str,
    health: dict,
    notes: str | None = None,
) -> TreatmentOutcome:
    if constraint_key not in ce.DIMENSIONS:
        raise ValueError(f"Unknown constraint key: {constraint_key}")
    if status not in _VALID_STATUS:
        raise ValueError(f"Invalid status: {status}")

    baseline_health = int(health.get("health_score", 0))
    baseline_dim = _dimension_score_from_health(health, constraint_key)
    treatment_id = _CONSTRAINT_TO_TRT.get(constraint_key)

    if status == "started":
        row = TreatmentOutcome(
            organization_id=org_id,
            constraint_key=constraint_key,
            treatment_id=treatment_id,
            status=status,
            baseline_health_score=baseline_health,
            baseline_dimension_score=baseline_dim,
            outcome_verdict="pending",
            notes=notes,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    # completed / abandoned — update most recent open started row for this constraint
    open_row = db.exec(
        select(TreatmentOutcome)
        .where(
            TreatmentOutcome.organization_id == org_id,
            TreatmentOutcome.constraint_key == constraint_key,
            TreatmentOutcome.status == "started",
        )
        .order_by(TreatmentOutcome.recorded_at.desc())
    ).first()

    if open_row is None:
        open_row = TreatmentOutcome(
            organization_id=org_id,
            constraint_key=constraint_key,
            treatment_id=treatment_id,
            status="started",
            baseline_health_score=baseline_health,
            baseline_dimension_score=baseline_dim,
            outcome_verdict="pending",
        )
        db.add(open_row)
        db.flush()

    open_row.status = status
    open_row.notes = notes or open_row.notes
    open_row.completed_at = datetime.now(timezone.utc)

    if status == "completed":
        snap = _latest_snapshot(db, org_id)
        snap_count = len(db.exec(
            select(DiagnosisSnapshot).where(DiagnosisSnapshot.organization_id == org_id)
        ).all())
        followup = None
        if snap:
            import json
            dims = json.loads(snap.dimensions_json or "{}")
            followup = dims.get(constraint_key)
        open_row.followup_dimension_score = followup
        open_row.outcome_verdict = _verdict(
            open_row.baseline_dimension_score,
            followup,
            snap_count,
        )
    else:
        open_row.outcome_verdict = "abandoned"

    db.add(open_row)
    db.commit()
    db.refresh(open_row)
    return open_row


def list_outcomes(db: Session, org_id: int) -> list[TreatmentOutcome]:
    return list(db.exec(
        select(TreatmentOutcome)
        .where(TreatmentOutcome.organization_id == org_id)
        .order_by(TreatmentOutcome.recorded_at.desc())
    ).all())


def outcome_to_dict(row: TreatmentOutcome) -> dict:
    label = ce.DIMENSIONS.get(row.constraint_key, {}).get("label", row.constraint_key)
    return {
        "id": row.id,
        "constraint_key": row.constraint_key,
        "constraint_label": label,
        "treatment_id": row.treatment_id,
        "status": row.status,
        "baseline_health_score": row.baseline_health_score,
        "baseline_dimension_score": row.baseline_dimension_score,
        "followup_dimension_score": row.followup_dimension_score,
        "outcome_verdict": row.outcome_verdict,
        "notes": row.notes,
        "recorded_at": row.recorded_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "protocol_id": OUTCOME_PROTOCOL_ID,
    }


def summarize_outcomes(rows: list[TreatmentOutcome]) -> dict:
    completed = [r for r in rows if r.status == "completed"]
    verdicts = [r.outcome_verdict for r in completed]
    return {
        "protocol_id": OUTCOME_PROTOCOL_ID,
        "total": len(rows),
        "active": sum(1 for r in rows if r.status == "started"),
        "completed": len(completed),
        "improved": verdicts.count("improved"),
        "unchanged": verdicts.count("unchanged"),
        "declined": verdicts.count("declined"),
        "insufficient_data": verdicts.count("insufficient_data"),
        "note": "Verdicts measure dimension score delta — not revenue outcomes until evidence confirms.",
    }
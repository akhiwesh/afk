"""
Evidence API — M3.1: upload business data, confirm the detected mapping,
store normalized evidence. Org-scoped everywhere.
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select, delete as sql_delete

from backend.app.core.database import get_session
from backend.app.core import evidence as ev
from backend.app.core import evidence_intel as evi
from backend.app.models.intelligence import EvidenceDataset, EvidenceRecord
from backend.app.models.auth import Organization, User
from backend.app.api.deps import get_current_user
from backend.app.api.intelligence import remember
from backend.app.bse.adapters.product import record_diagnosis_run, run_for_org
from backend.app.bse.projection import diagnosis_memory_payload

router = APIRouter(prefix="/intelligence/evidence", tags=["evidence"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB — decision-makers dump years of data


class ConfirmPayload(BaseModel):
    mapping: dict[str, str]   # {column_index: canonical_field}
    dataset_type: str


def _own_dataset(db: Session, dataset_id: int, org_id: int) -> EvidenceDataset:
    ds = db.get(EvidenceDataset, dataset_id)
    if not ds or ds.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/upload")
async def upload_evidence(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (25 MB max — split very large exports)")
    try:
        rows = ev.parse_file(file.filename or "upload.csv", content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    mapping = ev.detect_columns(rows)
    dtype = ev.infer_dataset_type(mapping)

    ds = EvidenceDataset(
        organization_id=current_user.organization_id,
        filename=file.filename or "upload.csv",
        dataset_type=dtype["type"],
        status="pending",
        row_count=len(rows) - 1,
        mapping_json=json.dumps(mapping),
        raw_json=json.dumps(rows),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)

    return {
        "dataset_id": ds.id,
        "filename": ds.filename,
        "row_count": ds.row_count,
        "detected_type": dtype,
        "columns": mapping,
        "needs_confirmation": dtype["needs_confirmation"] or any(c["needs_confirmation"] for c in mapping),
    }


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    rows = db.exec(
        select(EvidenceDataset)
        .where(EvidenceDataset.organization_id == current_user.organization_id)
        .order_by(EvidenceDataset.created_at.desc())
    ).all()
    return [{
        "id": d.id, "filename": d.filename, "dataset_type": d.dataset_type,
        "status": d.status, "row_count": d.row_count, "created_at": d.created_at.isoformat(),
    } for d in rows]


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
    ds = _own_dataset(db, dataset_id, current_user.organization_id)
    return {
        "id": ds.id, "filename": ds.filename, "dataset_type": ds.dataset_type,
        "status": ds.status, "row_count": ds.row_count,
        "columns": json.loads(ds.mapping_json),
        "type_options": ev.DATASET_TYPES,
        "field_options": [{"id": k, "label": v["label"]} for k, v in ev.CANONICAL_FIELDS.items()],
    }


@router.post("/datasets/{dataset_id}/confirm")
def confirm_dataset(dataset_id: int, payload: ConfirmPayload,
                    db: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
    ds = _own_dataset(db, dataset_id, current_user.organization_id)
    if ds.status == "confirmed":
        raise HTTPException(status_code=400, detail="Dataset already confirmed")
    if payload.dataset_type not in ev.DATASET_TYPES:
        raise HTTPException(status_code=422, detail="Unknown dataset type")
    bad = [f for f in payload.mapping.values() if f not in ev.CANONICAL_FIELDS]
    if bad:
        raise HTTPException(status_code=422, detail=f"Unknown fields: {bad}")

    rows = json.loads(ds.raw_json)
    records = ev.normalize_rows(rows, payload.mapping)
    if not records:
        raise HTTPException(status_code=422, detail="Mapping produced no usable records — check the column assignments.")

    for rec in records:
        db.add(EvidenceRecord(
            dataset_id=ds.id,
            organization_id=current_user.organization_id,
            record_date=rec.get("date"),
            amount=rec.get("amount"),
            data_json=json.dumps(rec),
        ))
    quality = evi.data_quality(records, payload.dataset_type)
    ds.status = "confirmed"
    ds.dataset_type = payload.dataset_type
    ds.mapping_json = json.dumps(payload.mapping)
    ds.raw_json = json.dumps({"quality": quality})  # raw dropped; quality kept
    ds.confirmed_at = datetime.now(timezone.utc)
    db.add(ds)
    db.commit()

    org_id = current_user.organization_id
    remember(db, org_id, "evidence_added",
             f"Evidence added: {ds.filename} ({ds.dataset_type}, {len(records)} records, "
             f"quality {round(quality['score']*100)}%).",
             {"dataset_id": ds.id, "kind": ds.dataset_type, "rows": len(records),
              "quality": quality["score"]})

    org = db.get(Organization, org_id)
    pipeline = run_for_org(db, org_id, org.name if org else None)
    diagnosed = record_diagnosis_run(db, org_id, pipeline)
    if diagnosed:
        clarity = pipeline.clarity
        primary = clarity["primary_constraint"]["label"]
        remember(db, org_id, "diagnosis_run",
                 f"Diagnosis updated after evidence: Revenue Health {clarity['health_score']}/100, "
                 f"primary constraint {primary}.",
                 diagnosis_memory_payload(pipeline))

    return {
        "confirmed": True,
        "records_stored": len(records),
        "dataset_type": ds.dataset_type,
        "quality": quality,
        "diagnosis_updated": diagnosed,
    }


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
    ds = _own_dataset(db, dataset_id, current_user.organization_id)
    db.exec(sql_delete(EvidenceRecord).where(EvidenceRecord.dataset_id == ds.id))
    db.delete(ds)
    db.commit()
    remember(db, current_user.organization_id, "evidence_removed",
             f"Evidence removed: {ds.filename} ({ds.dataset_type}).",
             {"kind": ds.dataset_type})
    return {"deleted": True}

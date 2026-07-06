"""Project pipeline outputs onto product persistence (snapshots, memory)."""
import json

from sqlmodel import Session

from backend.app.bse.contracts.diagnosis import PipelineOutput
from backend.app.models.intelligence import DiagnosisSnapshot


def persist_diagnosis_snapshot(db: Session, org_id: int, output: PipelineOutput) -> bool:
    """Write a DiagnosisSnapshot when the pipeline produces a sufficient diagnosis."""
    clarity = output.clarity
    if not clarity.get("sufficient"):
        return False

    dims = {
        d["key"]: d["score"]
        for d in clarity.get("dimensions", [])
        if d.get("score") is not None
    }
    primary = clarity.get("primary_constraint") or {}
    db.add(DiagnosisSnapshot(
        organization_id=org_id,
        health_score=clarity["health_score"],
        primary_constraint=primary.get("label", "Unknown"),
        dimensions_json=json.dumps(dims),
    ))
    db.commit()
    return True


def diagnosis_memory_payload(output: PipelineOutput) -> dict:
    clarity = output.clarity
    primary = clarity.get("primary_constraint") or {}
    return {
        "health_score": clarity.get("health_score"),
        "primary_constraint": primary.get("label"),
        "confidence": clarity.get("confidence"),
        "input_fingerprint": output.provenance.input_fingerprint,
        "engine_version": output.provenance.engine_version,
        "kb_release": output.provenance.kb_release,
    }
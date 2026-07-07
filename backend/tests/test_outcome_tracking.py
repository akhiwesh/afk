import json
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.app.knowledge_engine.outcome_tracking import record_outcome, OUTCOME_PROTOCOL_ID
from backend.app.knowledge_engine.registry import load_registry
from backend.app.models.intelligence import DiagnosisSnapshot
from backend.tests.test_engine import FULL_ANSWERS
from backend.app.core import engine as ce


def _auth(client: TestClient, email: str) -> dict:
    password = "StrongPass1"
    client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": "T",
        "organization_name": f"Org {email}",
    })
    tok = client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_out_protocol_in_registry():
    assert load_registry().get(OUTCOME_PROTOCOL_ID) is not None


def test_record_outcome_verdict_improved(session):
    health = ce.compute_health(FULL_ANSWERS)
    row = record_outcome(session, 9999, "conversion", "started", health)
    assert row.status == "started"
    assert row.baseline_dimension_score is not None
    now = datetime.now(timezone.utc)
    session.add(DiagnosisSnapshot(
        organization_id=9999,
        health_score=55,
        primary_constraint="Sales Conversion & Follow-up",
        dimensions_json=json.dumps({"conversion": row.baseline_dimension_score + 5}),
        created_at=now,
    ))
    session.commit()
    done = record_outcome(session, 9999, "conversion", "completed", health)
    assert done.outcome_verdict == "improved"
    assert done.followup_dimension_score == row.baseline_dimension_score + 5


def test_outcomes_api_flow(client: TestClient):
    h = _auth(client, "outcome@test.com")
    for qid, val in FULL_ANSWERS.items():
        if qid in {q["id"] for q in ce.QUESTIONS}:
            continue
    client.put("/api/intelligence/audit", json={"answers": FULL_ANSWERS}, headers=h)

    r = client.post("/api/intelligence/outcomes", json={
        "constraint_key": "conversion",
        "status": "started",
        "notes": "Installed follow-up system",
    }, headers=h)
    assert r.status_code == 200
    assert r.json()["outcome"]["outcome_verdict"] == "pending"

    listing = client.get("/api/intelligence/outcomes", headers=h)
    assert listing.status_code == 200
    assert listing.json()["summary"]["active"] >= 1

    traj = client.get("/api/intelligence/trajectory", headers=h)
    assert traj.status_code == 200
    assert "outcome_tracking" in traj.json()


def test_science_provenance_includes_outcome_protocol():
    h = ce.compute_health(FULL_ANSWERS)
    assert h["science_provenance"]["outcome_protocol_id"] == OUTCOME_PROTOCOL_ID
"""One-click demo session provisioning and auth."""
from fastapi.testclient import TestClient

from backend.app.core.seed import DEMO_EMAIL


def _demo_headers(client: TestClient) -> dict:
    r = client.post("/api/auth/demo")
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_demo_session_returns_token_and_flag(client: TestClient):
    r = client.post("/api/auth/demo")
    assert r.status_code == 200
    data = r.json()
    assert data["demo"] is True
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert data["user"]["email"] == DEMO_EMAIL
    assert data["user"]["organization_id"] is not None


def test_demo_session_idempotent(client: TestClient):
    r1 = client.post("/api/auth/demo").json()
    r2 = client.post("/api/auth/demo").json()
    assert r1["user"]["id"] == r2["user"]["id"]
    assert r1["user"]["organization_id"] == r2["user"]["organization_id"]


def test_demo_session_has_completed_audit_and_diagnosis(client: TestClient):
    h = _demo_headers(client)
    audit = client.get("/api/intelligence/audit", headers=h).json()
    assert audit["answered"] >= audit["total"] * 0.9

    health = client.get("/api/intelligence/health", headers=h).json()
    assert health["sufficient"] is True
    assert health.get("primary_constraint")
    assert health.get("health_score") is not None


def test_demo_me_endpoint(client: TestClient):
    h = _demo_headers(client)
    me = client.get("/api/auth/me", headers=h)
    assert me.status_code == 200
    assert me.json()["email"] == DEMO_EMAIL
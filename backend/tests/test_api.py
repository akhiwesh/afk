import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from typing import Generator

from backend.app.main import app
from backend.app.core.database import get_session
from backend.app.models.auth import User, UserRole

# Use separate test database in-memory.
# StaticPool is required: without it, every connection to sqlite :memory:
# gets a fresh empty database and tables created in fixtures disappear.
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "AFK Revenue Diagnostic"}

def test_auth_registration_and_login(client: TestClient):
    # 1. Register User
    reg_response = client.post("/api/auth/register", json={
        "email": "test@domain.com",
        "password": "MyPassword123",
        "full_name": "Test User",
        "organization_name": "Test Org"
    })
    assert reg_response.status_code == 200
    data = reg_response.json()
    assert data["email"] == "test@domain.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "admin"
    assert data["organization_id"] is not None

    # 2. Login User
    login_response = client.post("/api/auth/login", json={
        "email": "test@domain.com",
        "password": "MyPassword123"
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # 3. Request protected /me
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "test@domain.com"
    assert me_data["full_name"] == "Test User"


# ---------------------------------------------------------------------------
# Milestone 1 hardening tests
# ---------------------------------------------------------------------------

def _register(client, email="founder@afk.dev", password="StrongPass1"):
    return client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "AFK Founder",
        "organization_name": "AFK Inc",
    })


def test_weak_passwords_rejected(client: TestClient):
    # Too short
    r = _register(client, password="Ab1")
    assert r.status_code == 422
    # No digits
    r = _register(client, password="NoDigitsHere")
    assert r.status_code == 422
    # No uppercase
    r = _register(client, password="alllower123")
    assert r.status_code == 422


def test_duplicate_email_rejected(client: TestClient):
    assert _register(client).status_code == 200
    r = _register(client)
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


def test_wrong_password_rejected(client: TestClient):
    _register(client)
    r = client.post("/api/auth/login", json={
        "email": "founder@afk.dev", "password": "WrongPass1",
    })
    assert r.status_code == 401


def test_protected_route_requires_token(client: TestClient):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_garbage_token_rejected(client: TestClient):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


def test_unknown_api_route_is_404_not_null(client: TestClient):
    r = client.get("/api/this/does/not/exist")
    assert r.status_code == 404
    assert r.json() != None  # must be a JSON error body, never null


def test_spa_fallback_serves_index(client: TestClient):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_full_auth_cycle_cookie_and_logout(client: TestClient):
    _register(client)
    login = client.post("/api/auth/login", json={
        "email": "founder@afk.dev", "password": "StrongPass1",
    })
    assert login.status_code == 200
    assert "access_token" in login.cookies or "access_token" in login.json()
    # /me works via bearer token
    token = login.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "founder@afk.dev"
    # logout clears cookie without error
    out = client.post("/api/auth/logout")
    assert out.status_code == 200


# ---------------------------------------------------------------------------
# M2 — Revenue Intelligence API
# ---------------------------------------------------------------------------

def _auth_headers(client):
    _register(client, email="intel@afk.dev", password="StrongPass1")
    login = client.post("/api/auth/login", json={"email": "intel@afk.dev", "password": "StrongPass1"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_intelligence_requires_auth(client: TestClient):
    for ep in ["/api/intelligence/health", "/api/intelligence/twin",
               "/api/intelligence/audit", "/api/intelligence/audit/questions"]:
        assert client.get(ep).status_code == 401


def test_audit_save_and_health_lifecycle(client: TestClient):
    h = _auth_headers(client)
    # New org -> no evidence -> engine refuses to diagnose
    health = client.get("/api/intelligence/health", headers=h).json()
    assert health["sufficient"] is False

    # Unknown question ids rejected
    bad = client.put("/api/intelligence/audit", json={"answers": {"hacker_field": 1}}, headers=h)
    assert bad.status_code == 422

    # Save a substantial audit
    answers = {
        "business_type": "Distribution / trading", "team_size": 8,
        "growth_stage": "Growing (repeatable sales)",
        "monthly_revenue": 1500000, "revenue_model": "Repeat transactional (orders)",
        "leads_per_month": 25, "lead_sources_count": "One",
        "primary_lead_source": "Referrals / word of mouth", "marketing_active": "No",
        "qualification_process": "Informal gut-feel", "pct_leads_worth_it": 50,
        "conversion_close_rate": 30, "conversion_followups": "1",
        "conversion_owner": "Founder only",
        "conversion_process": "Mostly in people's heads", "conversion_cycle_days": 10,
        "pricing_confidence": "About right", "last_price_change": "More than a year ago",
        "discounting": "Sometimes",
        "repeat_rate": 20, "churn_reason_known": "No", "retention_process": "None",
        "founder_in_every_sale": "Yes, every deal", "documented_sales_process": "No",
    }
    r = client.put("/api/intelligence/audit", json={"answers": answers}, headers=h)
    assert r.status_code == 200 and r.json()["saved"] is True

    # Diagnosis now computes, with evidence-cited findings
    health = client.get("/api/intelligence/health", headers=h).json()
    assert health["sufficient"] is True
    assert health["primary_constraint"]["findings"]
    assert health["method_note"]

    # Twin mirrors the stated answers
    twin = client.get("/api/intelligence/twin", headers=h).json()
    assert twin["profile"]["business_type"] == "Distribution / trading"

    # Analyst answers deterministically without an LLM key, honestly labeled
    a = client.post("/api/intelligence/analyst", json={"question": "What is my bottleneck?"}, headers=h)
    assert a.status_code == 200
    body = a.json()
    assert body["mode"].startswith("deterministic")
    assert "What I believe:" in body["answer"]
    assert "Confidence:" in body["answer"]


def test_analyst_rejects_empty_question(client: TestClient):
    h = _auth_headers(client)
    assert client.post("/api/intelligence/analyst", json={"question": "  "}, headers=h).status_code == 422


def test_onboarding_checklist_for_new_founder(client: TestClient):
    h = _auth_headers(client)
    r = client.get("/api/intelligence/onboarding", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["audit_complete"] is False
    assert data["evidence_count"] == 0
    assert len(data["steps"]) == 3
    assert data["steps"][0]["id"] == "audit"

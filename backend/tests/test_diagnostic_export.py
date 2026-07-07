"""Tests for executive diagnosis PDF export."""
from fastapi.testclient import TestClient

from backend.app.core.diagnostic_export import build_diagnostic_pdf, export_filename


def _auth_headers(client: TestClient) -> dict:
    email = "pdf@test.dev"
    password = "StrongPass1"
    client.post("/api/auth/register", json={
        "email": email, "password": password,
        "full_name": "PDF Test", "organization_name": "PDF Test Co",
    })
    tok = client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _full_audit(client: TestClient, headers: dict):
    answers = {
        "business_type": "B2B services / agency", "team_size": 6,
        "growth_stage": "Early revenue (finding repeatability)",
        "monthly_revenue": 850000, "revenue_model": "Mixed",
        "leads_per_month": 14, "lead_sources_count": "One",
        "primary_lead_source": "Referrals / word of mouth", "marketing_active": "Sporadic",
        "qualification_process": "Informal gut-feel", "pct_leads_worth_it": 40,
        "conversion_close_rate": 22, "conversion_followups": "2",
        "conversion_owner": "Founder leads most deals",
        "conversion_process": "Mostly in people's heads", "conversion_cycle_days": 35,
        "pricing_confidence": "Probably underpriced", "last_price_change": "Never",
        "discounting": "Sometimes",
        "repeat_rate": 45, "churn_reason_known": "Partially / anecdotally",
        "retention_process": "Ad-hoc",
        "founder_in_every_sale": "Yes, every deal", "documented_sales_process": "No",
        "self_diagnosis": "We need more leads.",
        "biggest_worry": "Client concentration.",
    }
    r = client.put("/api/intelligence/audit", json={"answers": answers}, headers=headers)
    assert r.status_code == 200


def test_build_diagnostic_pdf_from_health_dict(client: TestClient):
    h = _auth_headers(client)
    _full_audit(client, h)
    health = client.get("/api/intelligence/health", headers=h).json()
    assert health["sufficient"] is True
    pdf = build_diagnostic_pdf(health, org_name="PDF Test Co")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 2000


def test_export_filename_slug():
    name = export_filename("Acme Corp!", __import__("datetime").datetime(2026, 7, 7, tzinfo=__import__("datetime").timezone.utc))
    assert name.startswith("afk-executive-diagnosis-acme-corp-20260707")
    assert name.endswith(".pdf")


def test_health_pdf_endpoint_requires_auth(client: TestClient):
    assert client.get("/api/intelligence/health/export.pdf").status_code == 401


def test_health_pdf_endpoint_insufficient(client: TestClient):
    h = _auth_headers(client)
    r = client.get("/api/intelligence/health/export.pdf", headers=h)
    assert r.status_code == 400
    assert "audit" in r.json()["detail"].lower() or "evidence" in r.json()["detail"].lower()


def test_health_pdf_endpoint_success(client: TestClient):
    h = _auth_headers(client)
    _full_audit(client, h)
    r = client.get("/api/intelligence/health/export.pdf", headers=h)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 2000
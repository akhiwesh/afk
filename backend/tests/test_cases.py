"""M3.5 CaseStudy pipeline — anonymization is fail-closed, approval is
founder-gated, the written object is registry-valid."""
import io
import pytest
from fastapi.testclient import TestClient

import backend.app.api.cases as cases_api
from backend.app.knowledge_engine.registry import _validate_object
import yaml


CSV = b"""Invoice No,Invoice Date,Party Name,Total Amount,Discount
I1,05/01/2026,Supersecret Distributors,"1,00,000",30000
I2,18/01/2026,Hushhush Traders,"80,000",20000
I3,02/02/2026,Supersecret Distributors,"1,20,000",40000
"""

ANSWERS = {"business_type": "Distribution / trading", "industry": "FMCG ice cream",
           "team_size": 8, "growth_stage": "Growing (repeatable sales)",
           "monthly_revenue": 1500000, "revenue_model": "Repeat transactional (orders)",
           "leads_per_month": 25, "lead_sources_count": "One",
           "primary_lead_source": "Referrals / word of mouth", "marketing_active": "No",
           "qualification_process": "Informal gut-feel", "pct_leads_worth_it": 50,
           "conversion_close_rate": 30, "conversion_followups": "1",
           "conversion_owner": "Founder only",
           "conversion_process": "Mostly in people's heads", "conversion_cycle_days": 10,
           "pricing_confidence": "About right", "last_price_change": "Never",
           "discounting": "Rarely", "repeat_rate": 20,
           "churn_reason_known": "No", "retention_process": "None",
           "founder_in_every_sale": "Yes, every deal", "documented_sales_process": "No"}


@pytest.fixture()
def org(client: TestClient, tmp_path, monkeypatch):
    monkeypatch.setattr(cases_api, "CASES_DIR", tmp_path)  # never write to the real KB in tests
    client.post("/api/auth/register", json={"email": "case@t.dev", "password": "StrongPass1",
                                            "full_name": "T", "organization_name": "TopSecret Ice Cream Co"})
    tok = client.post("/api/auth/login", json={"email": "case@t.dev", "password": "StrongPass1"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    client.put("/api/intelligence/audit", json={"answers": ANSWERS}, headers=h)
    up = client.post("/api/intelligence/evidence/upload",
                     files={"file": ("secretfile.csv", io.BytesIO(CSV), "text/csv")}, headers=h).json()
    mapping = {str(c["index"]): c["proposed"] for c in up["columns"]}
    client.post(f"/api/intelligence/evidence/datasets/{up['dataset_id']}/confirm",
                json={"mapping": mapping, "dataset_type": "invoices"}, headers=h)
    return h, tmp_path


def test_draft_is_anonymized(client: TestClient, org):
    h, _ = org
    d = client.post("/api/intelligence/cases/draft", headers=h)
    assert d.status_code == 200
    import json as j
    blob = j.dumps(d.json()).lower()
    assert "topsecret" not in blob          # org name gone
    assert "supersecret" not in blob        # customer names gone
    assert "hushhush" not in blob
    assert "secretfile" not in blob         # filename gone
    case = d.json()["case"]
    assert case["business_profile"]["revenue_band"] == "10L-25L"   # banded, not exact
    assert case["business_profile"]["team_band"] == "4-10"
    assert "1500000" not in blob            # exact revenue absent
    assert case["observation"]["health_score"] > 0
    assert case["contradictions"]           # repeat 20% claim vs measured, etc.


def test_approve_writes_valid_kb_object(client: TestClient, org):
    h, tmp = org
    case = client.post("/api/intelligence/cases/draft", headers=h).json()["case"]
    r = client.post("/api/intelligence/cases/approve",
                    json={"case": case, "consent": True}, headers=h)
    assert r.status_code == 200
    cid = r.json()["case_id"]
    files = list(tmp.glob("AFK-CAS-*.yaml"))
    assert len(files) == 1
    obj = yaml.safe_load(files[0].read_text())
    assert obj["id"] == cid and obj["status"] == "observed" and obj["synthetic"] is False
    assert _validate_object(obj, "case.yaml") == []   # registry-valid
    # memory event recorded
    tl = client.get("/api/intelligence/memory/timeline", headers=h).json()
    assert any(e["type"] == "case_contributed" for e in tl)


def test_approve_gates(client: TestClient, org):
    h, _ = org
    case = client.post("/api/intelligence/cases/draft", headers=h).json()["case"]
    # consent required
    assert client.post("/api/intelligence/cases/approve",
                       json={"case": case, "consent": False}, headers=h).status_code == 422
    # tampered case with an identifying term is rejected
    dirty = dict(case); dirty["notes"] = "client was Supersecret Distributors"
    assert client.post("/api/intelligence/cases/approve",
                       json={"case": dirty, "consent": True}, headers=h).status_code == 422
    # unauthenticated blocked (clear the session cookie the fixture login set)
    client.cookies.clear()
    assert client.post("/api/intelligence/cases/draft").status_code == 401

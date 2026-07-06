"""Sectional Revenue Diagnostic — per Business System micro-payoff."""
from fastapi.testclient import TestClient

from backend.app.core import audit_modules as am
from backend.tests.test_engine import FULL_ANSWERS


def _auth(client: TestClient, email: str) -> dict:
    password = "StrongPass1"
    reg = client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": "Tester",
        "organization_name": f"Org {email}",
    })
    assert reg.status_code == 200
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_modules_list_has_eight_systems():
    state = am.list_modules_state({})
    assert state["systems_total"] == 8
    assert len(state["modules"]) == 8
    assert state["modules"][0]["id"] == "context"
    assert state["modules"][1]["id"] == "demand"


def test_incomplete_module_payoff_asks_for_more():
    payoff = am.compute_module_payoff("demand", {})
    assert payoff["ready"] is False
    assert payoff["status"] == "incomplete"
    assert payoff["missing"]


def test_demand_module_payoff_with_full_answers():
    payoff = am.compute_module_payoff("demand", FULL_ANSWERS)
    assert payoff["ready"] is True
    assert payoff["dimension"]["key"] == "demand"
    assert payoff["dimension"]["score"] is not None
    assert payoff["verdict"]
    assert payoff.get("evidence_hint")


def test_context_module_non_diagnostic_payoff():
    answers = {k: v for k, v in FULL_ANSWERS.items()
               if k in am.module_question_ids(am.get_module("context"))}
    payoff = am.compute_module_payoff("context", answers)
    assert payoff["status"] == "captured"
    assert payoff["diagnostic"] is False


def test_module_save_returns_payoff(client: TestClient):
    h = _auth(client, "mod-audit@test.com")

    r = client.put("/api/intelligence/audit/modules/demand", json={
        "answers": {
            "leads_per_month": 5,
            "lead_sources_count": "One",
            "primary_lead_source": "Referrals / word of mouth",
            "marketing_active": "No",
        },
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["saved"] is True
    assert data["payoff"]["module_id"] == "demand"
    assert data["payoff"]["ready"] is True
    assert data["payoff"]["dimension"]["score"] is not None
    assert data["next_module"] == "qualification"


def test_module_save_rejects_wrong_questions(client: TestClient):
    h = _auth(client, "bad-audit@test.com")

    r = client.put("/api/intelligence/audit/modules/demand", json={
        "answers": {"team_size": 5},
    }, headers=h)
    assert r.status_code == 422


def test_conversion_module_payoff_includes_system_finding():
    payoff = am.compute_module_payoff("conversion", FULL_ANSWERS)
    assert payoff["ready"] is True
    assert payoff["dimension"]["key"] == "conversion"
    sf = payoff.get("system_finding")
    assert sf
    assert sf["score_line"].startswith("Score:")
    assert "Recommended Action" in sf["formatted"]


def test_get_audit_modules_endpoint(client: TestClient):
    h = _auth(client, "list-audit@test.com")

    r = client.get("/api/intelligence/audit/modules", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["systems_total"] == 8
    assert data["current_module"] == "context"
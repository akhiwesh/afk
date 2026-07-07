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
    assert state["modules"][1]["id"] == "reflection"
    assert state["modules"][2]["id"] == "demand"


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


def test_diagnostic_modules_all_include_system_finding():
    for module_id in ("demand", "qualification", "conversion", "pricing", "retention", "operations"):
        payoff = am.compute_module_payoff(module_id, FULL_ANSWERS)
        assert payoff.get("system_finding"), module_id
        assert payoff["system_finding"].get("formatted")


def test_optional_questions_surface_in_context_and_demand_modules():
    ctx = am.get_module("context")
    demand = am.get_module("demand")
    ctx_qids = {q["id"] for q in am.module_questions(ctx)}
    demand_qids = {q["id"] for q in am.module_questions(demand)}
    assert "gross_margin_band" in ctx_qids
    assert "cac_known" in demand_qids
    assert "gross_margin_band" not in am.module_question_ids(ctx)
    assert "cac_known" not in am.module_question_ids(demand)
    assert "gross_margin_band" in am.module_save_question_ids(ctx)
    assert "cac_known" in am.module_save_question_ids(demand)
    optional_flags = [q for q in am.module_questions(ctx) if q.get("optional")]
    assert any(q["id"] == "gross_margin_band" for q in optional_flags)


def test_demand_payoff_findings_carry_rule_ids():
    payoff = am.compute_module_payoff("demand", FULL_ANSWERS)
    ruled = [f for f in payoff.get("findings", []) if f.get("rule_id")]
    assert payoff.get("system_finding")
    assert len(ruled) >= 1
    assert all(f.get("rule_pack") == "kb-det-v1" for f in ruled)


def test_save_optional_cac_known_on_demand_module(client: TestClient):
    h = _auth(client, "opt-audit@test.com")
    r = client.put("/api/intelligence/audit/modules/demand", json={
        "answers": {
            "leads_per_month": 5,
            "lead_sources_count": "One",
            "primary_lead_source": "Referrals / word of mouth",
            "marketing_active": "No",
            "cac_known": "Rough estimate only",
        },
    }, headers=h)
    assert r.status_code == 200
    state = client.get("/api/intelligence/audit/modules", headers=h).json()
    assert state["answers"].get("cac_known") == "Rough estimate only"


def test_diagnosis_preview_includes_compound_findings():
    state = am.list_modules_state(FULL_ANSWERS)
    preview = state.get("diagnosis_preview")
    assert preview is not None
    assert preview.get("compound_findings")
    assert any(c.get("compound_id", "").startswith("AFK-CMP-") for c in preview["compound_findings"])


def test_get_audit_modules_endpoint(client: TestClient):
    h = _auth(client, "list-audit@test.com")

    r = client.get("/api/intelligence/audit/modules", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["systems_total"] == 8
    assert data["current_module"] == "context"
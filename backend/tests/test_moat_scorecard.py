from backend.app.knowledge_engine.moat_scorecard import compute_moat_scorecard, MOAT_SPEC_ID
from backend.app.knowledge_engine.registry import load_registry


def test_moat_spec_in_registry():
    assert load_registry().get(MOAT_SPEC_ID) is not None


def test_moat_scorecard_all_pillars_pass():
    card = compute_moat_scorecard()
    assert card["moat_spec_id"] == MOAT_SPEC_ID
    assert card["pillars_total"] == 7
    assert card["pillars_passed"] == 7
    assert card["moat_score"] == 100.0
    assert card["competitive_frame"]


def test_moat_api(client):
    client.post("/api/auth/register", json={
        "email": "moat@test.com", "password": "StrongPass1",
        "full_name": "T", "organization_name": "Moat",
    })
    tok = client.post("/api/auth/login", json={"email": "moat@test.com", "password": "StrongPass1"}).json()["access_token"]
    r = client.get("/api/knowledge/moat", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["moat_score"] == 100.0
"""Knowledge Engine — validation, auto-discovery, integrity, and PARITY:
the registry must contain exactly the knowledge the engine hard-codes."""
import pytest
from fastapi.testclient import TestClient

from backend.app.knowledge_engine.registry import (
    load_registry, KnowledgeError, _validate_object)
from backend.app.knowledge_engine.case_calibration import replay_priority_from_observation
from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi


def test_registry_loads_and_validates():
    r = load_registry()
    s = r.stats()
    assert s["total_objects"] >= 87
    assert s["by_type"].get("compound_pattern") == 3
    assert s["by_type"]["business_system"] == len(ce.DIMENSIONS)
    assert s["by_type"]["questionnaire_item"] == len(ce.QUESTIONS) + len(ce.OPTIONAL_QUESTIONS)
    assert s["by_type"]["treatment"] == len(ce._CONSTRAINT_PLAYBOOK)


def test_everything_is_honest_hypothesis_with_provenance():
    r = load_registry()
    for oid in r.all_ids():
        o = r.get(oid)
        assert o["status"] == "hypothesis"          # nothing can claim more yet
        assert o["created"]["reason"]                # provenance mandatory
        assert o["version"] in ("1.0.0", "1.1.0", "1.2.0")


def test_no_dangling_relationships():
    load_registry(strict=True)  # raises on any dangling edge


def test_schema_rejects_bad_objects():
    bad = {"id": "WRONG", "type": "constraint", "name": "x", "version": "1",
           "status": "truth", "owner": "me", "created": {}, "description": "d"}
    errs = _validate_object(bad, "test.yaml")
    assert any("AFK-XXX-0000" in e for e in errs)
    assert any("semver" in e for e in errs)
    assert any("validation ladder" in e for e in errs)
    assert any("created.by" in e for e in errs)


def test_PARITY_registry_matches_running_engine():
    """The bridge to migration: knowledge files must equal engine internals."""
    r = load_registry()
    # every engine dimension exists as a system with the same audit fields
    systems = {o["name"]: o for o in r.by_type("business_system")}
    for key, meta in ce.DIMENSIONS.items():
        assert meta["label"] in systems
        assert systems[meta["label"]]["audit_fields"] == meta["fields"]
    # every audit question extracted with identical field id and options
    ques = {o["engine_field"]: o for o in r.by_type("questionnaire_item")}
    for q in ce.QUESTIONS:
        assert q["id"] in ques
        assert ques[q["id"]].get("options") == q.get("options")
        assert ques[q["id"]].get("scored") is not False
    for q in ce.OPTIONAL_QUESTIONS:
        assert q["id"] in ques
        assert ques[q["id"]].get("options") == q.get("options")
        assert ques[q["id"]].get("scored") is False
    # every treatment's uplift matches the playbook verbatim
    trts = r.by_type("treatment")
    uplifts = sorted(t["expected_outcome"]["uplift_heuristic_fraction_of_annual_revenue"] for t in trts)
    assert uplifts == sorted(p["uplift"] for p in ce._CONSTRAINT_PLAYBOOK.values())
    for i, (key, play) in enumerate(ce._CONSTRAINT_PLAYBOOK.items(), start=1):
        trt = r.get(f"AFK-TRT-{i:04d}")
        eo = trt["expected_outcome"]
        assert eo["fixability"] == play["fixability"]
        assert eo["time_to_impact_days"] == play["time_to_impact_days"]
    # the confidence model records the live ceiling
    cfm = r.get("AFK-CFM-0001")
    assert cfm["questionnaire_ceiling"] == evi.QUESTIONNAIRE_CEILING
    # priority model matches engine selection method
    pri = r.get("AFK-PRI-0001")
    assert pri["type"] == "priority_model"
    assert ce.PRIORITY_MODEL_ID == pri["id"]
    sample = ce.compute_constraint_priority("conversion", 25)
    assert sample["model_id"] == pri["id"]


def test_cas_0001_calibration_probe_without_evidence_metrics():
    """Base PRI-0001 diverges from recorded primary — documents the gap."""
    r = load_registry()
    case = r.get("AFK-CAS-0001")
    replay = replay_priority_from_observation(case["observation"])
    assert replay["replayable"]
    assert replay["recorded_primary"] == "Pricing & Monetization"
    assert replay["aligned_with_lowest_score"] is True
    assert replay["aligned_with_impact_priority"] is False
    assert replay["engine_primary_key"] == "conversion"
    assert replay["divergence"]


def test_cas_0001_calibration_probe_with_invoice_metrics_aligns():
    """Evidence adjunct reconciles N=1 case when stored invoice metrics are replayed."""
    r = load_registry()
    case = r.get("AFK-CAS-0001")
    metrics = {
        "avg_discount_pct": case["computed_metrics"]["avg_discount_pct"],
    }
    replay = replay_priority_from_observation(case["observation"], metrics)
    assert replay["aligned_with_impact_priority"] is True
    assert replay["engine_primary_key"] == "pricing"
    assert replay["evidence_adjustments_applied"]["pricing"]["exposure_multiplier"] > 1.0


def test_todos_mark_gaps_instead_of_inventions():
    r = load_registry()
    trt = r.by_type("treatment")[0]
    assert any("contraindications" in t for t in trt["todos"])  # gap marked, not assumed absent


def test_knowledge_api(client: TestClient):
    assert client.get("/api/knowledge/stats").status_code == 401  # auth required, checked BEFORE login
    client.post("/api/auth/register", json={"email": "kb@t.dev", "password": "StrongPass1",
                                            "full_name": "T", "organization_name": "KB"})
    tok = client.post("/api/auth/login", json={"email": "kb@t.dev", "password": "StrongPass1"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    stats = client.get("/api/knowledge/stats", headers=h).json()
    assert stats["total_objects"] >= 78
    res = client.get("/api/knowledge/search?q=pricing&type=detection_rule", headers=h).json()
    assert res and all(r["type"] == "detection_rule" for r in res)
    obj = client.get("/api/knowledge/objects/AFK-CON-0004", headers=h).json()
    assert obj["name"].startswith("Pricing")
    rel = client.get("/api/knowledge/objects/AFK-CON-0004/relationships", headers=h).json()
    assert rel["incoming"]  # detection rules point at it
    assert client.get("/api/knowledge/objects/AFK-XXX-9999", headers=h).status_code == 404


# ---- M3.4: Business Memory ----------------------------------------------

def test_business_memory_timeline(client: TestClient):
    import io
    client.post("/api/auth/register", json={"email": "mem@t.dev", "password": "StrongPass1",
                                            "full_name": "T", "organization_name": "Mem"})
    tok = client.post("/api/auth/login", json={"email": "mem@t.dev", "password": "StrongPass1"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    # audit save -> event(s)
    client.put("/api/intelligence/audit", json={"answers": {"team_size": 5}}, headers=h)
    # evidence add + remove -> events
    csv = b"Invoice No,Invoice Date,Party Name,Total Amount\nI1,05/01/2026,Acme,50000\nI2,08/01/2026,Beta,60000\n"
    up = client.post("/api/intelligence/evidence/upload",
                     files={"file": ("i.csv", io.BytesIO(csv), "text/csv")}, headers=h).json()
    mapping = {str(c["index"]): c["proposed"] for c in up["columns"]}
    client.post(f"/api/intelligence/evidence/datasets/{up['dataset_id']}/confirm",
                json={"mapping": mapping, "dataset_type": "invoices"}, headers=h)
    client.delete(f"/api/intelligence/evidence/datasets/{up['dataset_id']}", headers=h)

    tl = client.get("/api/intelligence/memory/timeline", headers=h).json()
    types = [e["type"] for e in tl]
    assert "audit_saved" in types
    assert "evidence_added" in types
    assert "evidence_removed" in types
    for e in tl:
        assert e["summary"] and e["at"]
    # newest first
    assert tl == sorted(tl, key=lambda e: e["at"], reverse=True)
    # org isolation
    client.post("/api/auth/register", json={"email": "mem2@t.dev", "password": "StrongPass1",
                                            "full_name": "T", "organization_name": "Mem2"})
    tok2 = client.post("/api/auth/login", json={"email": "mem2@t.dev", "password": "StrongPass1"}).json()["access_token"]
    assert client.get("/api/intelligence/memory/timeline",
                      headers={"Authorization": f"Bearer {tok2}"}).json() == []

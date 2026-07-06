"""M3.2 — metrics, contradictions, evidence-weighted confidence, quality, drivers."""
import io
from fastapi.testclient import TestClient
from backend.app.core import evidence_intel as evi

INVOICES = [
    {"invoice_id": "1", "date": "2026-01-05", "customer": "Sharma Distributors", "amount": 100000.0, "discount": 30000.0},
    {"invoice_id": "2", "date": "2026-01-18", "customer": "Mehta Traders", "amount": 80000.0, "discount": 20000.0},
    {"invoice_id": "3", "date": "2026-02-02", "customer": "Sharma Distributors", "amount": 120000.0, "discount": 40000.0},
    {"invoice_id": "4", "date": "2026-02-20", "customer": "Kwality Depot", "amount": 90000.0, "discount": 25000.0},
]
BELIEFS = {"pricing_confidence": "About right", "discounting": "Rarely",
           "repeat_rate": 80, "monthly_revenue": 850000, "avg_deal_value": 500000}


def test_metrics_carry_basis():
    m = evi.compute_metrics({"invoices": INVOICES})
    assert m["avg_discount_pct"]["value"] > 20
    assert "invoices" in m["avg_discount_pct"]["basis"]
    assert m["repeat_customer_rate"]["value"] > 0
    for v in m.values():
        assert v["basis"]


def test_contradictions_belief_vs_evidence():
    m = evi.compute_metrics({"invoices": INVOICES})
    cons = evi.detect_contradictions(BELIEFS, m)
    kinds = {c["evidence"]["metric"] for c in cons}
    assert "avg_discount_pct" in kinds          # "pricing about right" vs ~24% discount
    assert "repeat_customer_rate" in kinds      # stated 80% vs measured ~33%
    assert "avg_monthly_revenue" in kinds       # stated 8.5L vs ~1.95L in invoices
    for c in cons:
        assert c["belief"]["answer"] is not None
        assert c["evidence"]["basis"]
        assert c["explanation"]
        assert c["follow_up_question"]          # cross-examination built in
        # tone: compares, never accuses
        assert "lying" not in c["explanation"].lower()


def test_no_contradictions_without_evidence():
    assert evi.detect_contradictions(BELIEFS, {}) == []


def test_confidence_increases_with_evidence():
    answers = {q_id: "x" for q_id in ["pricing_confidence", "last_price_change", "discounting"]}
    base = evi.evidence_confidence(answers, {}, {})
    with_inv = evi.evidence_confidence(answers, {"invoices": 100}, {"invoices": 0.95})
    assert with_inv["per_dimension"]["pricing"] > base["per_dimension"]["pricing"]
    assert with_inv["overall"] > base["overall"]
    # questionnaire alone can never exceed its ceiling on evidence-verifiable dims
    assert base["per_dimension"]["pricing"] <= evi.QUESTIONNAIRE_CEILING + 0.01
    assert "hypotheses" in with_inv["sources"]["Questionnaire"]["weight"]


def test_poor_quality_lowers_confidence():
    answers = {"pricing_confidence": "About right"}
    good = evi.evidence_confidence(answers, {"invoices": 100}, {"invoices": 1.0})
    bad = evi.evidence_confidence(answers, {"invoices": 100}, {"invoices": 0.4})
    assert bad["per_dimension"]["pricing"] < good["per_dimension"]["pricing"]


def test_data_quality_names_reasons():
    messy = INVOICES + [{"invoice_id": "5", "customer": "sharma distributors."},  # no amount/date, near-dupe name
                        {"invoice_id": "6", "customer": "New Co"}]
    q = evi.data_quality(messy, "invoices")
    assert q["score"] < 1.0
    assert any("amount" in r for r in q["reasons"])


def test_drivers_found():
    m = evi.compute_metrics({"invoices": INVOICES,
                             "leads": [{"source": "Referral", "status": "won"},
                                       {"source": "Referral", "status": "won"},
                                       {"source": "Ads", "status": "lost"}]})
    d = evi.detect_drivers(m)
    labels = [x["label"] for x in d]
    assert any("channel" in l for l in labels)
    assert all(x["basis"] for x in d)


def test_missing_evidence_guidance():
    me = evi.missing_evidence({"invoices": 50})
    pricing = next(x for x in me if x["dimension"] == "Pricing & Monetization")
    demand = next(x for x in me if x["dimension"] == "Demand Generation")
    assert pricing["covered"] is True
    assert demand["covered"] is False and "export" in demand["suggestion"]


# ---- API integration: the full loop ---------------------------------------

INVOICE_CSV = b"""Invoice No,Invoice Date,Party Name,Total Amount,Discount
INV-1,05/01/2026,Sharma Distributors,"1,00,000",30000
INV-2,18/01/2026,Mehta Traders,"80,000",20000
INV-3,02/02/2026,Sharma Distributors,"1,20,000",40000
INV-4,20/02/2026,Kwality Depot,"90,000",25000
"""


def test_health_reflects_evidence_after_upload(client: TestClient):
    client.post("/api/auth/register", json={"email": "m32@t.dev", "password": "StrongPass1",
                                            "full_name": "T", "organization_name": "M32"})
    tok = client.post("/api/auth/login", json={"email": "m32@t.dev", "password": "StrongPass1"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Audit with beliefs that the invoices will contradict
    answers = {"business_type": "B2B services / agency", "team_size": 5,
               "growth_stage": "Growing (repeatable sales)", "monthly_revenue": 900000,
               "revenue_model": "Mixed", "avg_deal_value": 150000,
               "leads_per_month": 20, "lead_sources_count": "Two or three",
               "primary_lead_source": "Referrals / word of mouth", "marketing_active": "Sporadic",
               "qualification_process": "Informal gut-feel", "pct_leads_worth_it": 50,
               "conversion_close_rate": 25, "conversion_followups": "4–5",
               "conversion_owner": "Mostly team",
               "conversion_process": "Fully documented + used", "conversion_cycle_days": 20,
               "pricing_confidence": "About right", "last_price_change": "More than a year ago",
               "discounting": "Rarely", "repeat_rate": 85,
               "churn_reason_known": "Partially / anecdotally", "retention_process": "Ad-hoc",
               "founder_in_every_sale": "Most deals", "documented_sales_process": "No"}
    client.put("/api/intelligence/audit", json={"answers": answers}, headers=h)

    before = client.get("/api/intelligence/health", headers=h).json()
    assert before["contradictions"] == []

    up = client.post("/api/intelligence/evidence/upload",
                     files={"file": ("inv.csv", io.BytesIO(INVOICE_CSV), "text/csv")}, headers=h).json()
    mapping = {str(c["index"]): c["proposed"] for c in up["columns"]}
    conf = client.post(f"/api/intelligence/evidence/datasets/{up['dataset_id']}/confirm",
                       json={"mapping": mapping, "dataset_type": "invoices"}, headers=h).json()
    assert "quality" in conf

    after = client.get("/api/intelligence/health", headers=h).json()
    # Confidence rose with evidence
    assert after["confidence"] > before["confidence"]
    assert after["confidence_breakdown"]["sources"]["Invoices"]["rows"] == 4
    # Contradictions detected: pricing belief vs ~24% discounts, repeat 85% vs ~33%
    metrics_hit = {c["evidence"]["metric"] for c in after["contradictions"]}
    assert "avg_discount_pct" in metrics_hit
    assert "repeat_customer_rate" in metrics_hit
    # Analyst (deterministic) surfaces the contradiction
    a = client.post("/api/intelligence/analyst", json={"question": "Is my pricing fine?"}, headers=h).json()
    assert "contradicts" in a["answer"]

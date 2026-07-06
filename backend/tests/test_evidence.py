"""M3.1 Evidence Engine — parsing, detection, normalization, API lifecycle."""
import io
from backend.app.core import evidence as ev
from fastapi.testclient import TestClient


INVOICE_CSV = b"""Invoice No,Invoice Date,Party Name,Total Amount,Discount,Status
INV-001,03/01/2026,Sharma Distributors,"1,45,000",5000,Paid
INV-002,15/01/2026,Mehta Traders,"98,500",0,Paid
INV-003,28/01/2026,Kwality Depot West,"2,10,000",21000,Pending
"""

LEADS_CSV = b"""Name,Email,Lead Source,Stage
Rohit K,rohit@acme.in,Referral,Qualified
Priya S,priya@zenith.co,LinkedIn Outbound,New
Arjun M,arjun@dmart.com,Referral,Lost
"""

JUNK_CSV = b"only one column and no data rows\n"


def test_parse_csv_handles_indian_formats():
    rows = ev.parse_file("invoices.csv", INVOICE_CSV)
    assert rows[0][0] == "Invoice No"
    assert len(rows) == 4
    assert ev.to_number("1,45,000") == 145000.0
    assert ev.to_iso_date("03/01/2026") == "2026-01-03"


def test_detect_columns_invoices():
    rows = ev.parse_file("invoices.csv", INVOICE_CSV)
    cols = {c["header"]: c for c in ev.detect_columns(rows)}
    assert cols["Invoice No"]["proposed"] == "invoice_id"
    assert cols["Invoice Date"]["proposed"] == "date"
    assert cols["Party Name"]["proposed"] == "customer"
    assert cols["Total Amount"]["proposed"] == "amount"
    assert cols["Status"]["proposed"] == "status"
    # every proposal explains itself
    for c in cols.values():
        assert c["reason"]
    t = ev.infer_dataset_type(list(cols.values()))
    assert t["type"] == "invoices"


def test_detect_columns_leads_and_email_by_values():
    rows = ev.parse_file("leads.csv", LEADS_CSV)
    cols = {c["header"]: c for c in ev.detect_columns(rows)}
    assert cols["Email"]["proposed"] == "email"
    assert cols["Lead Source"]["proposed"] == "source"
    assert ev.infer_dataset_type(list(cols.values()))["type"] == "leads"


def test_normalize_never_invents():
    rows = ev.parse_file("invoices.csv", INVOICE_CSV)
    mapping = {"0": "invoice_id", "1": "date", "2": "customer", "3": "amount", "4": "discount", "5": "status"}
    recs = ev.normalize_rows(rows, mapping)
    assert len(recs) == 3
    assert recs[0]["amount"] == 145000.0
    assert recs[0]["date"] == "2026-01-03"
    # Unparseable numeric stays None rather than a guess
    bad = ev.normalize_rows([["amt"], ["not-a-number"]], {"0": "amount"})
    assert bad[0]["amount"] is None


def test_junk_file_rejected():
    try:
        ev.parse_file("junk.csv", JUNK_CSV)
        assert False, "should have raised"
    except ValueError:
        pass


# ---- API lifecycle ---------------------------------------------------------

def _auth(client, email):
    client.post("/api/auth/register", json={
        "email": email, "password": "StrongPass1",
        "full_name": "T", "organization_name": f"Org {email}"})
    r = client.post("/api/auth/login", json={"email": email, "password": "StrongPass1"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_upload_confirm_lifecycle_and_isolation(client: TestClient):
    h1 = _auth(client, "a@ev.dev")
    up = client.post("/api/intelligence/evidence/upload",
                     files={"file": ("invoices.csv", io.BytesIO(INVOICE_CSV), "text/csv")},
                     headers=h1)
    assert up.status_code == 200
    body = up.json()
    ds_id = body["dataset_id"]
    assert body["row_count"] == 3
    assert body["detected_type"]["type"] == "invoices"

    # Confirm with the proposed mapping
    mapping = {str(c["index"]): c["proposed"] for c in body["columns"]}
    conf = client.post(f"/api/intelligence/evidence/datasets/{ds_id}/confirm",
                       json={"mapping": mapping, "dataset_type": "invoices"}, headers=h1)
    assert conf.status_code == 200
    assert conf.json()["records_stored"] == 3

    # Shows up in list, and in the diagnosis's evidence sources
    ls = client.get("/api/intelligence/evidence/datasets", headers=h1).json()
    assert ls[0]["status"] == "confirmed"
    health = client.get("/api/intelligence/health", headers=h1).json()
    assert any(s["kind"] == "invoices" for s in health["evidence_sources"])

    # Org isolation: another org cannot see or touch it
    h2 = _auth(client, "b@ev.dev")
    assert client.get(f"/api/intelligence/evidence/datasets/{ds_id}", headers=h2).status_code == 404
    assert client.delete(f"/api/intelligence/evidence/datasets/{ds_id}", headers=h2).status_code == 404
    assert client.get("/api/intelligence/evidence/datasets", headers=h2).json() == []

    # Double confirm rejected; bad field rejected
    assert client.post(f"/api/intelligence/evidence/datasets/{ds_id}/confirm",
                       json={"mapping": mapping, "dataset_type": "invoices"}, headers=h1).status_code == 400


def test_upload_rejects_garbage(client: TestClient):
    h = _auth(client, "c@ev.dev")
    r = client.post("/api/intelligence/evidence/upload",
                    files={"file": ("junk.csv", io.BytesIO(JUNK_CSV), "text/csv")}, headers=h)
    assert r.status_code == 422

"""
Evidence Engine — M3.1: ingestion, column detection, normalization.

Design contract:
  * Pure functions: bytes/rows in, structured proposals out. No DB, no I/O.
  * Detection is explainable: every proposed column mapping carries a
    confidence and the reason it was chosen.
  * When uncertain, the system proposes and ASKS — it never silently guesses.
"""
import csv
import io
import re
from datetime import datetime
from typing import Optional

# Canonical fields every dataset normalizes into. This vocabulary is the
# contract with M3.2 (confidence + contradiction) and M4 (benchmarks).
CANONICAL_FIELDS = {
    "date":       {"label": "Date"},
    "amount":     {"label": "Amount (₹)"},
    "discount":   {"label": "Discount"},
    "customer":   {"label": "Customer / company name"},
    "email":      {"label": "Email"},
    "phone":      {"label": "Phone"},
    "status":     {"label": "Status / stage"},
    "source":     {"label": "Lead source / channel"},
    "product":    {"label": "Product / service"},
    "quantity":   {"label": "Quantity"},
    "invoice_id": {"label": "Invoice / order ID"},
    "notes":      {"label": "Notes"},
    "ignore":     {"label": "Ignore this column"},
}

# Header-name synonyms -> canonical field
_HEADER_SYNONYMS = {
    "date": ["date", "invoice date", "created", "created at", "order date", "txn date",
             "transaction date", "payment date", "closed date", "timestamp", "month"],
    "amount": ["amount", "total", "revenue", "value", "price", "invoice amount", "net amount",
               "grand total", "sale value", "deal value", "payment", "paid", "amt", "total amount"],
    "discount": ["discount", "disc", "discount %", "discount amount", "rebate"],
    "customer": ["customer", "client", "company", "name", "account", "party", "customer name",
                 "client name", "buyer", "party name"],
    "email": ["email", "e-mail", "email address", "mail"],
    "phone": ["phone", "mobile", "contact", "phone number", "whatsapp"],
    "status": ["status", "stage", "state", "pipeline stage", "deal stage", "lead status", "outcome"],
    "source": ["source", "channel", "lead source", "origin", "utm source", "campaign", "medium", "referrer"],
    "product": ["product", "item", "service", "sku", "plan", "description", "particulars"],
    "quantity": ["quantity", "qty", "units", "count"],
    "invoice_id": ["invoice", "invoice no", "invoice id", "invoice number", "order id",
                   "order no", "bill no", "receipt", "ref", "reference", "id", "voucher no"],
}

_DATE_PATTERNS = [
    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S",
    "%d/%m/%y", "%m-%d-%Y",
]

_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")
_PHONE_RE = re.compile(r"^\+?[\d\s()-]{8,15}$")


def parse_file(filename: str, content: bytes) -> list[list[str]]:
    """Parse CSV or Excel bytes into rows of strings. Raises ValueError on
    unsupported/corrupt files."""
    name = filename.lower()
    if name.endswith((".xlsx", ".xlsm")):
        import openpyxl
        try:
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        except Exception as e:
            raise ValueError(f"Could not read Excel file: {e}")
        ws = wb.active
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(["" if c is None else str(c).strip() for c in row])
            if len(rows) >= 5001:
                break
        wb.close()
    elif name.endswith((".csv", ".txt", ".tsv")):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        delimiter = "\t" if name.endswith(".tsv") or "\t" in text.splitlines()[0] else ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = [[c.strip() for c in r] for r in reader]
        rows = rows[:5001]
    else:
        raise ValueError("Unsupported file type. Upload a .csv, .tsv, or .xlsx file.")

    rows = [r for r in rows if any(c for c in r)]
    if len(rows) < 2:
        raise ValueError("File needs a header row and at least one data row.")
    return rows


def _try_date(v: str) -> bool:
    v = v.strip()
    if not v:
        return False
    for p in _DATE_PATTERNS:
        try:
            datetime.strptime(v, p)
            return True
        except ValueError:
            continue
    return False


def _try_number(v: str) -> bool:
    v = v.strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("INR", "").strip()
    if not v:
        return False
    try:
        float(v)
        return True
    except ValueError:
        return False


def to_number(v: str) -> Optional[float]:
    v = str(v).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("INR", "").strip()
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def to_iso_date(v: str) -> Optional[str]:
    v = str(v).strip()
    for p in _DATE_PATTERNS:
        try:
            return datetime.strptime(v, p).date().isoformat()
        except ValueError:
            continue
    return None


def detect_columns(rows: list[list[str]]) -> list[dict]:
    """Propose a canonical mapping for each column with confidence + reason."""
    header, data = rows[0], rows[1:51]  # sample first 50 data rows
    out = []
    for idx, raw_name in enumerate(header):
        name = (raw_name or "").strip().lower()
        values = [r[idx] for r in data if idx < len(r) and r[idx]]
        proposal, conf, reason = "ignore", 0.0, "No recognizable header or values."

        # 1. Header-name match (strong signal)
        for field, syns in _HEADER_SYNONYMS.items():
            if name in syns:
                proposal, conf, reason = field, 0.95, f'Header "{raw_name}" matches known name.'
                break
            if any(s in name for s in syns if len(s) > 3):
                proposal, conf, reason = field, 0.7, f'Header "{raw_name}" resembles known name.'
                break

        # 2. Value-based inference (confirms or proposes)
        if values:
            n = len(values)
            date_pct = sum(_try_date(v) for v in values) / n
            num_pct = sum(_try_number(v) for v in values) / n
            email_pct = sum(bool(_EMAIL_RE.match(v.strip())) for v in values) / n
            phone_pct = sum(bool(_PHONE_RE.match(v.strip())) for v in values) / n

            if email_pct >= 0.8:
                proposal, conf, reason = "email", max(conf, 0.95), "Values look like email addresses."
            elif date_pct >= 0.8:
                if proposal in ("ignore", "date"):
                    proposal, conf, reason = "date", max(conf, 0.9), "Values parse as dates."
            elif phone_pct >= 0.8 and proposal == "ignore":
                proposal, conf, reason = "phone", 0.85, "Values look like phone numbers."
            elif num_pct >= 0.9 and proposal == "ignore":
                proposal, conf, reason = "amount", 0.5, "Values are numeric — could be amount, quantity, or an ID. Please confirm."
            elif proposal != "ignore" and proposal in ("amount", "discount", "quantity") and num_pct < 0.5:
                conf, reason = 0.35, f'Header suggests {proposal} but values are mostly not numeric. Please confirm.'

        out.append({
            "index": idx,
            "header": raw_name,
            "proposed": proposal,
            "confidence": round(conf, 2),
            "reason": reason,
            "needs_confirmation": conf < 0.8,
            "samples": values[:3],
        })
    return out


def infer_dataset_type(mapping: list[dict]) -> dict:
    """Infer what kind of business data this is from the mapped fields."""
    fields = {m["proposed"] for m in mapping if m["proposed"] != "ignore"}
    if "invoice_id" in fields and "amount" in fields:
        t, conf = "invoices", 0.9
    elif "amount" in fields and "date" in fields and "source" not in fields:
        t, conf = "transactions", 0.7
    elif "source" in fields or ("status" in fields and "amount" not in fields):
        t, conf = "leads", 0.75
    elif "email" in fields or "customer" in fields:
        t, conf = "customers", 0.6
    else:
        t, conf = "unknown", 0.3
    return {"type": t, "confidence": conf,
            "needs_confirmation": conf < 0.8,
            "reason": f"Based on detected fields: {', '.join(sorted(fields)) or 'none'}."}


DATASET_TYPES = ["invoices", "transactions", "leads", "customers", "unknown"]


def normalize_rows(rows: list[list[str]], mapping: dict[int, str]) -> list[dict]:
    """Apply a confirmed {column_index: canonical_field} mapping.
    Numbers and dates are coerced; unparseable cells become None (never invented)."""
    header, data = rows[0], rows[1:]
    out = []
    for r in data:
        rec = {}
        for idx_str, field in mapping.items():
            idx = int(idx_str)
            if field == "ignore" or idx >= len(r):
                continue
            raw = r[idx].strip() if r[idx] else ""
            if not raw:
                continue
            if field in ("amount", "discount", "quantity"):
                rec[field] = to_number(raw)
            elif field == "date":
                rec[field] = to_iso_date(raw)
            else:
                rec[field] = raw
        if rec:
            out.append(rec)
    return out

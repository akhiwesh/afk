# MILESTONE REPORT — M3.1: Evidence Ingestion
**Date:** 4 July 2026 · **Status:** ✅ Complete · **Tests:** 32/32 · **Delivery gates:** module-graph ✓ · test suite ✓ · fresh boot ✓ · fresh-unzip install-and-boot ✓ (new process — every future zip passes all four before reaching you)

## Executive summary
AFK can now eat real business data. Founders upload CSV/TSV/Excel exports — Zoho, Tally, Stripe, plain spreadsheets — and AFK detects what each column means, says how sure it is and *why*, asks for confirmation when uncertain, and normalizes everything into one canonical evidence model (dates, amounts, customers, sources, statuses…). This is the raw material for M3.2's dynamic confidence and the Contradiction Engine: audit answers are what the founder *believes*; these records are what the business *did*.

## What was built
- **Parsing** — CSV/TSV/Excel; UTF-8 & Latin-1; Indian number formats (`1,45,000`, `₹`, `Rs.`) and 12 date formats; 5MB/5,000-row cap for v1.
- **Column detection** — header-synonym matching + value-based inference (emails, dates, phones, numerics). Every proposal carries confidence + a plain-English reason; anything under 80% is flagged "Please confirm." Ambiguity is honest: a numeric column with a vague header proposes at 50% and asks.
- **Dataset-type inference** — invoices / transactions / leads / customers, with stated reasoning, founder-overridable.
- **Confirm-then-normalize lifecycle** — raw rows held only until the founder confirms the mapping; then normalized `EvidenceRecord`s are stored and raw data is dropped. Unparseable cells become empty, never guessed.
- **Evidence page** — upload → mapping review (per-column dropdowns, confidence badges, sample values) → confirm → evidence-on-record list with remove.
- **Diagnosis integration (minimal, by design)** — Executive Diagnosis now lists all evidence sources on record. Evidence-weighted confidence is M3.2's job.

## Verified live (not just unit-tested)
Uploaded a messy Indian-format invoice CSV → all 6 columns detected at 95% → confirmed → 3 normalized records stored → diagnosis immediately lists "live_invoices.csv | invoices | 3 rows" alongside the audit.

## APIs added
`POST /intelligence/evidence/upload` · `GET /datasets` · `GET /datasets/{id}` · `POST /datasets/{id}/confirm` · `DELETE /datasets/{id}` — all org-scoped, cross-org access returns 404 (tested).

## Tests added (+7)
Indian formats · invoice & lead detection · normalization-never-invents · junk rejection · full upload→confirm lifecycle with org isolation · garbage upload 422. Shared fixtures moved to `conftest.py`.

## Intentionally NOT built (and why)
- **Live connectors (Zoho/Stripe APIs)** — file export covers the same evidence at 5% of the complexity; connectors need OAuth apps + credentials (founder decision, later).
- **PDF invoice parsing** — OCR quality would violate never-invent; CSV/Excel exports are lossless.
- **Multi-sheet Excel** — first sheet only for v1; flagged to the user implicitly by row counts.
- **Evidence→score integration** — deliberately deferred to M3.2 so confidence math gets designed properly, not bolted on.

## Technical debt
- `raw_json` holds full file rows while pending (fine ≤5k rows; revisit if caps rise). Old test_api.py keeps a duplicate local fixture (harmless, cleanup later).

## Next: M3.2 — Evidence Engine
Dynamic evidence-weighted confidence (questionnaire 40% ceiling, invoices→100% on revenue claims), and the Contradiction Engine ("founder says pricing is fine; invoices show 35% average discount").

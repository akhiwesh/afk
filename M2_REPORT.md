# MILESTONE REPORT — M2: Diagnosis
**Date:** 3 July 2026 · **Status:** ✅ Complete · **Tests:** 20/20 passing (13 M1 + 7 engine) · **App:** boots clean, all M2 endpoints verified live

## Executive summary
AFK is no longer a generic SaaS. Logging in now lands on **Revenue Health** — an editorial diagnosis screen, not a dashboard. Behind it sits a deterministic **Constraint Engine** that scores six revenue dimensions from the founder's own audit answers, names the primary constraint, estimates the opportunity (formula shown), and recommends one concrete next step. Every conclusion cites its evidence. If evidence is missing, the product says **"Not enough evidence"** — it never invents. All previously fabricated data (fake charts, fake KPI deltas, ten canned AI assistants) is gone from the product surface.

## What was built
1. **Revenue Audit** — 28-question structured intake across 9 sections (profile, revenue model, demand, qualification, sales & follow-up, pricing, retention, operations, goals/self-diagnosis). Partial answers valid; unknown fields rejected at the API.
2. **Business Twin** — structured company profile computed verbatim from audit answers (explicitly not AI output), with constraints, strengths, and completeness.
3. **Revenue Health** — the hero screen: score /100, risk level, primary constraint, confidence, revenue opportunity (with its formula displayed), recommended next step, evidence-cited findings, all-dimension breakdown, and a method note explaining exactly how scores are computed.
4. **Constraint Engine V1** — pure, deterministic, rule-based (`backend/app/core/engine.py`). Six dimensions: Demand, Qualification, Conversion & Follow-up, Pricing, Retention, Founder Dependency. Each dimension starts at 100; ~17 named rules subtract stated penalties. Per-dimension confidence = audit coverage; dimensions under 50% coverage are *unscored* rather than guessed.
5. **The Analyst** — one AI replacing ten assistants. Every answer: What I believe / Why / Confidence / Missing information / Suggested next question. LLM mode when `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` is set; otherwise an honest **deterministic mode** that reports the engine's computed findings and says so. LLM failures fall back to computed truth, labeled.
6. **Navigation collapse** — sidebar is now: Revenue Health · Revenue Audit · Business Twin · Revenue Data · Analyst · Settings. Projects, AI Studio, Content Studio, Automations, Billing removed from the surface (code archived, not deleted). `#dashboard` redirects to `#health`. Fabricated chart data stripped from the analytics endpoint.

## Why
Constitution compliance: diagnose before prescribing; one analyst, not ten assistants; every number explainable; no fake data anywhere; Apple-Health-not-dashboard.

## How to test every feature (founder walkthrough)
1. `python run.py` → open http://127.0.0.1:8000 → login `admin@afk.agency` / `password123`
2. You land on **Revenue Health**: demo org scores **75/100, Low Risk**, primary constraint **Pricing & Monetization**, opportunity **₹12.24L/yr** with the formula shown under it. Scroll: evidence chips under every finding, then all six dimension bars with confidence.
3. **Revenue Audit**: change "Honest read on your pricing" to "Premium and defensible" and "When did prices last change" to "Within the last year" → Save & Diagnose → Health recomputes live and the constraint moves (to Founder Dependency). Change answers back or explore.
4. **Business Twin**: profile mirrors your answers; constraints/strengths lists match Health.
5. **Analyst**: ask "Why is revenue stuck?" → structured 5-part answer, honestly labeled "Deterministic mode" (no LLM key set). Ask with an empty audit org (register a new account) → it refuses to guess and points to the audit.
6. **Register a new org** → Health shows "Not enough evidence" with exactly what's missing — the never-invent rule, visible.

## Files changed
**New:** `backend/app/models/intelligence.py`, `backend/app/core/engine.py`, `backend/app/api/intelligence.py`, `backend/tests/test_engine.py`, `frontend/js/pages/{health,audit,twin,analyst}.js`
**Modified:** `main.py` (router), `database.py` (table), `seed.py` (demo audit — stated answers, everything computed from them), `analytics.py` (fabricated chart removed), `app.js` (nav + routes), `login.js`/`landing.js` (redirect to #health), `test_api.py` (+3 M2 tests)

## Test results
20/20: auth suite (13) · engine unit tests (7: refuses to guess on empty input; every finding carries evidence + reasoning; opportunity only exists with revenue evidence; partial dimensions unscored; twin mirrors answers; founder dependency detected) · API lifecycle (auth-gated, unknown-field rejection, save→diagnose→twin→analyst).

## Risks / debt
- Rule penalties and benchmarks (e.g., <15% close rate) are v1 heuristics from operator judgment — they need calibration against real audits (that's M4, Benchmark Engine).
- Analyst LLM mode is implemented but untested against a live key (none configured) — needs one real key smoke test.
- Old modules are archived, not deleted; DB still creates their tables. Harmless; cleanup in a later milestone.
- CRM page still says "CRM Pipeline" internally on its own header; nav label is Revenue Data. Cosmetic.

## Next milestone — M3: Evidence Engine
Connect real data (CRM records, invoices) into the diagnosis so evidence ≠ questionnaire-only; founder-uploaded data (CSV) as evidence; per-finding drill-down.

## Founder action items
1. Run the walkthrough above (10 minutes) — especially step 3, watching the constraint move when evidence changes. That's the product.
2. Your audit questions, in your words — still the most valuable input you can give. My 28 questions are a competent skeleton; yours carry Vintech's scars.
3. LLM key decision when ready (Anthropic recommended; the Analyst is wired for it).

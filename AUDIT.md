# AFK — Product & Engineering Audit
**Prepared by:** Founding CTO · **Date:** 3 July 2026 · **Basis:** full read of all 9 backend modules, 7 data models, seed data, and 11 frontend pages (~4,000 lines) against the AFK Constitution

---

## Executive summary

The codebase is a competently built **generic agency SaaS** — a small HubSpot with a Kanban board, ten canned AI assistants, a workflow simulator, and an invoice list. The engineering foundation (auth, organizations, roles, database layer) is solid after M1 and worth keeping. The product on top of it fails the constitution's core test on almost every screen: nothing in the current app helps a founder understand *why* revenue isn't growing.

There is one finding that matters more than all others, and it is existential for a company selling intelligence:

> **The current product systematically fabricates data.** The dashboard chart shows invented revenue for Jan–May. Every KPI card displays a hardcoded "↑ 12% vs last month" that is computed from nothing. The ten AI assistants return pre-written paragraphs regardless of what the user asks. The workflow engine returns fake success outputs (`record_id: 999`) for actions it never performed.

For a normal SaaS demo this is cosmetic. For a **Revenue Intelligence** company it is brand-fatal: the first sophisticated founder who notices the numbers are fake will never trust an AFK diagnosis again. Rule one going forward: **AFK never displays a number it didn't compute, and never states a conclusion it can't explain.** Honest emptiness ("not enough data — here's what we need") beats fake certainty. That principle alone will differentiate us more than any feature.

The good news: roughly 60% of the code survives — as chassis and as *evidence store* — and the pivot is a focused rebuild of the intelligence layer plus the home screen, not a rewrite.

---

## Module-by-module verdicts

| Module | What it is today | Verdict | Reasoning |
|---|---|---|---|
| **Auth, Orgs, Roles** | JWT auth, org-scoped users, admin/team/client roles (hardened in M1) | **KEEP** | Foundation for everything. Production-grade after M1. Untouched. |
| **CRM** (clients, pipeline stages, notes) | HubSpot-lite contact manager | **REPURPOSE** | As a *product*, it loses to Zoho forever. As an *evidence store* — the funnel data the Analyst diagnoses from — it's exactly what we need. Keep the data model and CRUD; demote it in the UI from "CRM" to "Revenue Data". Stop competing; start ingesting. |
| **Finance** (invoices, fake "pay" button) | Pretend billing with no payment rails | **REPURPOSE data / REMOVE billing UI** | Invoices are revenue ground-truth — critical evidence for diagnosis. But the "Pay" button that just flips a status flag is theater. Keep the model, kill the pretend-billing page. |
| **Analytics dashboard** | 4 KPI cards + revenue chart, ~half the numbers fabricated | **REDESIGN → becomes the hero screen** | This becomes Revenue Health: score, primary constraint, revenue at risk, confidence — the "health report" from the constitution. All fabricated data removed. Real numbers or explicit "insufficient data". |
| **AI: 10 assistants + mock responses** | Ten personas returning canned paragraphs; Gemini fallback | **REMOVE & REDESIGN** | Directly violates the constitution ("one outstanding analyst > ten average assistants"). The mock-response dictionary is the single worst asset in the codebase — it *performs* intelligence. Replace with **one Analyst** grounded in the org's actual data, always showing evidence + confidence + what data is missing. |
| **Content studio** (copywriting generator) | Generic AI copywriter | **REMOVE** | Pure off-mission. A founder can get this from ChatGPT. It actively signals "another AI tool". Delete from nav; archive code. |
| **Automation / workflow builder** | Visual workflow with a *simulated* executor returning fake outputs | **PARK** | The constitution says we are not an automation platform. But "recommended experiments" (a constitutional requirement) may one day want an execution layer. Remove from product surface; keep the data model dormant. No further investment. |
| **Projects / Kanban / tasks** | Asana-lite | **REMOVE from product** | Zero connection to revenue diagnosis. Every hour here is an hour Linear already won. Remove from nav; archive code. (If future audits produce "action plans", a far simpler action list will come back — designed for that, not as generic Kanban.) |
| **Admin** (user list, audit logs, feature flags) | Org user management + in-memory flags | **SIMPLIFY** | Keep user management. Feature flags are stored in a Python dict — they silently reset on every restart (a bug pretending to be a feature). Remove flags and the manual audit-log endpoint until needed. |
| **Landing page** | "Scale Your Business At The Speed of AI", fake client logos (Stark, Wayne, Cyberdyne), pricing for a product that doesn't exist | **REDESIGN (later milestone)** | Messaging sells the *old* generic-SaaS positioning. Fictional logos on a trust-based product are a liability. Redesign after the product proves the new story — product first, landing second. |

**Net effect on the app:** navigation shrinks from ~9 sections to ~4 — **Revenue Health · Analyst · Revenue Data · Settings.** That shrinkage *is* the strategy. A founder who opens AFK should see a diagnosis, not a toolbox.

---

## Engineering audit (independent of product direction)

**Sound and staying:** M1 security posture (env-driven secrets, password policy, atomic registration, org-scoped queries with consistent 404-on-cross-org access — I verified the pattern in every module). SQLite + SQLModel is right for this stage. The no-framework, template-string frontend is unfashionable but fast to change and has zero build step; acceptable prototype debt, revisit only if we hire frontend engineers.

**Debt worth logging, not fixing yet:** counting rows via `len(query.all())` instead of SQL COUNT (fine under ~10k rows); no pagination on list endpoints; no login rate-limiting; 7-day tokens with no refresh flow; docstring-level test coverage on business modules (tests cover auth well, business logic barely).

**Decisions the rebuild forces:**
1. **LLM provider.** The code hardcodes Gemini. The Analyst is the product now, so this is a real decision: quality of reasoning matters more than cost at the prototype stage. Needs an API key either way — **founder input required** (this is a genuine credentials + budget stop under our operating rules).
2. **Where evidence comes from.** At prototype stage the honest answer is: a structured **audit intake** (the founder answers ~20 diagnostic questions about their funnel, pricing, follow-up discipline, retention) combined with whatever real CRM/invoice data exists in the org. Integrations (importing from actual Zoho/Tally/Sheets) come later. The intake *is* the product's data-collection mechanism, and it doubles as your consulting instrument.

---

## The one product decision I want to challenge before building

The constitution's journey is right: *founder conversations → audit → framework → methodology → software.* But note what's first. The fastest way to make the software good is for **you to deliver two audits manually** — to RTS Labs and ThirdEye, or two distributors from the Vintech network — using a structured intake and your own analysis, with me as your analyst in the background. Every question they stumble on, every insight that lands, becomes the spec. The prototype I build next should be **the tool you use to deliver those audits**, which then becomes self-serve. Building the self-serve version before one real founder has been diagnosed inverts the constitution's own sequence. I'll build either way — but the CEO's highest-leverage act this month is a delivered audit, not a reviewed prototype.

---

## Proposed next milestone — M2: "The Diagnosis"

Transform the app so that within five minutes a founder experiences: **intake → Revenue Health score → primary constraint → evidence → what to do next → what data is missing.**

1. **Audit intake** — structured diagnostic questionnaire (the digitized version of your Revenue Engine Audit)
2. **Revenue Health home screen** — score /100, risk level, primary constraint, estimated revenue at risk, confidence; calm, editorial, Apple-Health-not-dashboard
3. **Constraint engine v1** — transparent, rule-based scoring across funnel stages (deterministic and explainable *by design*; the LLM layers on top, it doesn't replace the math)
4. **The Analyst** — one AI, grounded in the org's intake + CRM + invoice evidence, every answer carrying "why I believe this / confidence / what's missing"
5. **Navigation collapse** — remove Projects, Content, Automation, Billing from the product surface
6. All fabricated numbers deleted app-wide

**Explicitly not in M2:** integrations, payments, landing redesign, mobile.

## Founder action items
1. Approve/amend the Keep–Repurpose–Remove table above (5 min)
2. LLM provider decision + API key (I'll give you options and costs when you're ready)
3. Send me the questions you'd ask a distributor or founder in a real revenue audit — even 10 rough voice-note bullets. That list becomes the intake, and the intake becomes the product.
4. The two outreach emails. Still the highest-leverage send in the company.

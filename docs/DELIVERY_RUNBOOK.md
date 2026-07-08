# AFK Revenue Constraint Diagnostic — Delivery Runbook

**Version:** 1.0  
**Last updated:** July 2026  
**Offer:** Concierge Revenue Constraint Diagnostic · ₹49,000 · 2-week engagement  
**Instrument:** AFK Platform (`#audit` → `#evidence` → `#diagnosis` → `#twin`)

This runbook is for the **founder-operator** delivering the diagnostic. AFK is the instrument; you are the interpreter, quality gate, and client relationship.

---

## 1. Principles (read before every engagement)

1. **Evidence over narrative.** The engine says *insufficient* rather than guessing. Your job is to help the client supply evidence — not to override the engine with consultant storytelling.
2. **One primary constraint.** AFK ranks by revenue exposure × fixability, not “lowest score wins.” Walk the client through *why* that constraint ranked first.
3. **Show your work.** Every finding cites audit answers or uploaded data. On the diagnosis call, open the platform and point at evidence chips — do not paraphrase from memory.
4. **Directional ranges, not promises.** Opportunity figures are heuristics with formulas shown. Never quote a single “you’re leaving ₹X on the table” number without the range and basis.
5. **Treatment ≠ implementation.** You deliver clarity and a 90-day protocol. You do not run their sales motion, ads, or CRM.
6. **Calibration is honest.** Benchmark percentiles and cross-case claims stay disabled until `calibration_ready` — do not imply industry rankings we cannot defend.

---

## 2. Roles

| Role | Owner | Responsibility |
|------|--------|----------------|
| **Delivery lead** | AFK founder | Fit call, diagnosis session, QA, client comms |
| **Client founder** | Customer | Audit answers, evidence exports, treatment execution |
| **Platform** | AFK | Deterministic diagnosis, PDF, outcome tracking (AFK-OUT-0001) |

---

## 3. Fit criteria

### Accept when

- B2B services / agency / consultancy with a **repeatable offer**
- Approx. **₹5L–₹25L/mo** revenue (flexible if evidence-rich)
- Founder still involved in sales or delivery
- Can export **at least one** of: invoices, CRM/leads, transactions (CSV/Excel, &lt;5 MB)
- Understands this is **diagnosis**, not done-for-you GTM

### Decline (politely) when

- Pre-revenue or no repeatable offer
- Wants CRM, automation, outbound tooling, or “run it for us”
- Refuses to share any business data (audit-only is possible but cap expectations)
- Expects guaranteed revenue uplift or investor-grade forecasts
- Enterprise procurement / legal review cycles beyond 2 weeks (offer a scoped pilot later)

### Fit reply SLA

**Within 1 business day** of `OfferInquiry` receipt.

---

## 4. Engagement timeline

| Phase | Days | Client-facing name |
|-------|------|-------------------|
| Intake & fit | 0–2 | Application review + fit call |
| Evidence collection | 2–7 | Revenue Audit + uploads |
| Diagnosis delivery | 7–10 | Executive diagnosis session |
| Treatment handoff | 10–14 | Protocol start + checkpoint schedule |
| Checkpoint (included) | ~Day 90 | Follow-up diagnosis |

**Clock starts** on payment confirmation (or signed scope + 50% deposit if you use one).

---

## 5. Phase 0 — Application intake

### Where applications land

- **UI:** `#offer` → “Apply for diagnostic” modal
- **API:** `POST /api/offer/inquiry`
- **DB:** `offerinquiry` table

### Review checklist (15 min)

- [ ] Company + email look real (not disposable domain)
- [ ] Revenue band in target range (or strong strategic reason)
- [ ] `primary_worry` is a revenue constraint, not “need a website”
- [ ] No obvious mismatch (ecommerce-only, pure product SaaS with no services motion)

### Pull recent applications (SQLite local)

```sql
SELECT id, full_name, email, company, revenue_band, primary_worry, created_at
FROM offerinquiry
ORDER BY created_at DESC
LIMIT 20;
```

### Outcomes

| Decision | Action |
|----------|--------|
| **Fit** | Send fit-call invite (template §12) |
| **Not fit** | Send decline template (template §12) |
| **Unclear** | One clarifying email; do not book call until resolved |

---

## 6. Phase 1 — Fit call (30 minutes)

**Goal:** Confirm scope, evidence availability, and timeline. Do not diagnose on this call.

### Agenda

1. **Context (5 min)** — Business model, team size, revenue band, offer
2. **Their hypothesis (5 min)** — What they think is wrong (`self_diagnosis` preview)
3. **Evidence check (10 min)** — What exports exist today? Who will upload?
4. **Process (5 min)** — Walk through 2-week timeline and deliverables
5. **Close (5 min)** — Payment / kickoff date, platform access plan

### Evidence minimum (set expectations)

| Priority | File | Unlocks |
|----------|------|---------|
| **Required** | Completed Revenue Audit (in-platform) | Baseline diagnosis |
| **High** | Invoice export (12 mo if possible) | Pricing, retention, discount contradictions |
| **High** | CRM / lead export | Demand, qualification, conversion metrics |
| **Nice** | Transaction or customer list | Repeat rate, concentration |

If they only have audit answers: **proceed** but say clearly that confidence stays capped (~40% per dimension) until evidence is uploaded.

### Fit call exit criteria

- [ ] Client agrees to 2-week cadence
- [ ] Named person will upload files (usually founder)
- [ ] Payment path agreed
- [ ] Kickoff date in calendar

---

## 7. Phase 2 — Platform setup (Day 0–1)

### Option A — Client registers (default)

1. Send link: `{BASE_URL}/#register`
2. Client creates org (becomes admin)
3. You receive login **only if they invite you** — prefer **screen-share** on diagnosis call instead of sharing passwords

### Option B — You provision (concierge)

1. Register org on their behalf with their work email (get written consent)
2. Hand off credentials once; require password change
3. Never use `POST /api/auth/demo` for paying clients — demo org is synthetic only

### Client navigation (send in kickoff email)

```
1. Revenue Audit     →  #audit
2. Upload evidence   →  #evidence
3. Diagnosis         →  #diagnosis
4. Business Twin     →  #twin
```

### Kickoff email must include

- [ ] Links above
- [ ] Evidence export how-to (§8)
- [ ] Deadline: audit complete by Day 5, evidence by Day 7
- [ ] Diagnosis session hold (Day 8–10)

---

## 8. Phase 3 — Evidence collection (Days 2–7)

### Revenue Audit

- **Route:** `#audit`
- **Modules:** Context → Hypothesis → Demand → Qualification → Conversion → Pricing → Retention → Operations
- **Target:** 100% questions answered (or ≥90% with explicit gaps noted)
- **Nudge at Day 4** if `onboarding` checklist shows audit incomplete

### Evidence upload

- **Route:** `#evidence`
- **Formats:** CSV, TSV, Excel · max **5 MB** / ~5,000 rows
- **Flow:** Upload → review column mapping → **Confirm** (pending datasets do not affect diagnosis)

| Dataset type | Typical source | Confirms |
|--------------|----------------|----------|
| `invoices` | Zoho/FreshBooks/Excel export | Discount %, AOV, monthly revenue |
| `leads` | CRM export | Volume, sources, funnel |
| `transactions` | Payment gateway / ERP | Close rate, timing |
| `customers` | CRM accounts | Repeat rate, concentration |

### Operator checks (you, async)

```bash
# After client confirms uploads — review in UI or API as admin if needed
GET /api/intelligence/onboarding   # audit_complete, evidence_count, diagnosis_ready
GET /api/intelligence/health       # sufficient, primary_constraint, confidence
GET /api/intelligence/twin         # profile mirrors audit answers
```

### Red flags

| Signal | Action |
|--------|--------|
| `sufficient: false` after full audit | Client missing ≥35% audit — schedule 15-min audit completion call |
| Zero confirmed evidence | Remind: diagnosis works but confidence stays low; send sample export screenshots |
| Upload pending confirmation | Client stuck on mapping — offer 10-min screen-share |
| Contradictions panel empty + invoices uploaded | Verify dataset status = `confirmed` |

---

## 9. Phase 4 — Pre-diagnosis QA (Day 7, internal)

**Do not book the executive session until this pass is complete.**

### QA checklist

- [ ] `GET /api/intelligence/health` → `sufficient: true`
- [ ] Primary constraint has ≥1 finding with evidence citations
- [ ] `method_note` and confidence visible on diagnosis page
- [ ] If invoices present: check for belief vs data contradictions (pricing, retention)
- [ ] Revenue opportunity (if shown) has **basis** text — read it; sanity-check against stated monthly revenue
- [ ] Download PDF: `GET /api/intelligence/health/export.pdf` — readable, no blank sections
- [ ] Business Twin (`#twin`) reflects stated profile

### Manual interpretation (your value-add)

Prepare 3 talking points **before** the call:

1. **What they believe** — `self_diagnosis` / `biggest_worry` from audit
2. **What the data says** — primary constraint + top contradiction (if any)
3. **What to do first** — playbook `next_step` for primary constraint (from engine, not improvised)

Playbook reference (constraint → first move):

| Constraint key | First move (from engine) |
|----------------|--------------------------|
| `demand` | One new lead source for 30 days before spending on ads |
| `qualification` | 3 disqualifying questions in first conversation |
| `conversion` | Next-touch date on every lead; 5 touches before close-lost |
| `pricing` | Quote 15–20% higher to next 3 **new** prospects only |
| `retention` | Five churn calls: “what changed?” — no selling |
| `founder_dependency` | Record 3 sales calls → one-page written playbook |

### When diagnosis is weak

| Situation | Delivery approach |
|-----------|-------------------|
| Audit-only, no files | Deliver with explicit “low confidence” framing; prescribe evidence uploads as Week 1 of treatment |
| Partial evidence | Diagnose what we can; list ranked upload CTAs from diagnosis page |
| Client hypothesis ≠ primary constraint | Lead with cross-examination — this is the highest-value moment |

---

## 10. Phase 5 — Diagnosis session (60 minutes, Days 8–10)

**Format:** Screen-share with client logged in (or you presenting their `#diagnosis`).

### Agenda

| Segment | Time | Content |
|---------|------|---------|
| Open | 5 min | Recap goal: one primary constraint, evidence-based |
| Health score | 10 min | Score, risk level, confidence — what would raise confidence |
| Primary constraint | 15 min | Finding cards, evidence chips, why ranked #1 |
| Contradictions | 10 min | Belief vs data (if any) |
| Dimension tour | 10 min | Weakest systems — only those with findings |
| Opportunity range | 5 min | Formula and directional band — not a guarantee |
| Next 90 days | 10 min | Playbook step + start treatment in-platform |
| Close | 5 min | PDF sent, checkpoint date, support boundary |

### Live actions on the call

1. Walk through `#diagnosis` top to bottom
2. Export PDF together (client sees download)
3. Click **Start this treatment** on recommendation card (`POST /api/intelligence/outcomes`, status `started`, protocol **AFK-OUT-0001**)
4. Confirm treatment appears on `#twin` outcomes block
5. Schedule **Day-90 checkpoint** (calendar invite)

### Do not

- Promise specific ₹ uplift
- Claim benchmark percentiles
- Suggest AFK will run implementation
- Diagnose dimensions with zero coverage as if certain

---

## 11. Phase 6 — Treatment handoff (Days 10–14)

### Deliverables package (send within 24h of session)

| # | Deliverable | Source |
|---|-------------|--------|
| 1 | Executive diagnosis PDF | `#diagnosis` → Download PDF |
| 2 | Primary constraint summary | Your 1-page email (template §12) |
| 3 | 90-day protocol | Playbook `next_step` + client's chosen treatment ID (AFK-TRT-*) |
| 4 | Checkpoint date | ~90 days from `started` outcome |

### Treatment tracking

- **Protocol:** AFK-OUT-0001
- **States:** `started` → `completed` | `abandoned`
- **Verdict** (on complete): compares dimension score vs baseline — `improved` | `unchanged` | `declined` | `insufficient_data`
- Client can mark complete in UI; you review on checkpoint

### Engagement close checklist

- [ ] PDF delivered
- [ ] Treatment `started` in platform
- [ ] Day-90 checkpoint scheduled
- [ ] Invoice / payment reconciled
- [ ] Internal case notes captured (§13)

---

## 12. Phase 7 — Day-90 checkpoint (included)

**Goal:** Re-run diagnosis and compare dimension movement — not revenue claims.

### 2 weeks before checkpoint

- Email client: upload fresh evidence (optional), confirm they’re still executing protocol
- Ask: any major structural changes (pricing overhaul, new offer, layoffs)?

### Checkpoint session (30 min)

1. Open `#diagnosis` — new health score vs baseline snapshot
2. Review `#twin` trajectory / outcomes verdict
3. If `insufficient_data`: more time or evidence needed — do not force a verdict
4. Mark treatment `completed` or `abandoned` in UI with notes
5. Offer **paid follow-on** only if they want ongoing clarity — no hard sell

---

## 13. Client email templates

### Fit — accepted

```
Subject: AFK Revenue Diagnostic — fit confirmed, next steps

Hi {name},

Thanks for applying. Based on what you shared about {company}, this is a good fit for the Revenue Constraint Diagnostic.

Next step: a 30-minute fit call to confirm evidence on hand and lock dates.
{calendar_link}

Investment: ₹49,000 · 2-week engagement · includes Day-90 checkpoint.

— {your_name}
```

### Fit — declined

```
Subject: AFK Revenue Diagnostic — not the right fit right now

Hi {name},

Thanks for your interest. Based on {reason: pre-revenue / tooling expectations / no exportable data}, we’re not the right fit for this diagnostic today.

What might help instead: {brief alternative — e.g. complete audit via demo at {url}/#offer, revisit when revenue is ₹5L+/mo}.

— {your_name}
```

### Kickoff — platform access

```
Subject: Kickoff — AFK Revenue Diagnostic for {company}

Hi {name},

Clock starts today. Here’s your path:

1. Complete Revenue Audit: {url}/#audit (target: Day 5)
2. Upload evidence: {url}/#evidence — invoices + CRM if you have them (target: Day 7)
3. We meet for diagnosis: {diagnosis_call_datetime}

Exports: CSV or Excel, last 12 months if possible. Max 5 MB per file.

Reply if you get stuck on exports — happy to do a 10-min screen-share.

— {your_name}
```

### Post-diagnosis — deliverables

```
Subject: Your Revenue Constraint Diagnostic — {company}

Hi {name},

Primary constraint: {constraint_label} ({health_score}/100, {risk_level})

Attached: executive diagnosis PDF.

Your 90-day first move: {playbook_next_step}

We started treatment tracking in your workspace (AFK-OUT-0001). Day-90 checkpoint: {date}.

This is directional clarity, not a revenue guarantee. Execution is yours — we measure dimension movement on the next diagnosis.

— {your_name}
```

---

## 14. Edge cases

| Scenario | Handling |
|----------|----------|
| Client ghosts after payment | Pause clock; one follow-up at Day 7 and Day 14; offer partial refund policy (define in scope doc) |
| Client demands refund mid-engagement | If no diagnosis delivered → partial refund; if delivered → no refund, checkpoint still honored |
| “Just tell me what to fix” before audit | Redirect to audit — engine refuses to guess |
| Wants you to implement playbook | Out of scope; refer to their team or partner |
| Evidence shows fraud / fabricated data | Stop engagement; do not certify diagnosis |
| AI analyst questions during engagement | OK for exploration; label answers as deterministic/evidence-grounded — not a substitute for diagnosis |
| Multiple stakeholders | One admin account; diagnosis session requires decision-maker |

---

## 15. Internal post-engagement (calibration flywheel)

After each paid diagnostic:

- [ ] Capture anonymized case summary (constraint, score, evidence types, verdict at Day 90)
- [ ] Note founder-approved? (required before case enters calibration set)
- [ ] Log contradictions that were most persuasive — informs future sales copy
- [ ] Track time spent vs ₹49,000 — target &lt;12 hours total delivery time by case 5

**Do not** add client data to benchmark pool without explicit consent.

---

## 16. Time budget (target)

| Activity | Hours |
|----------|-------|
| Intake + fit call | 1.0 |
| Async monitoring + nudges | 1.5 |
| Pre-diagnosis QA | 0.5 |
| Diagnosis session | 1.0 |
| Pack-up + email | 0.5 |
| Day-90 checkpoint | 0.5 |
| **Total** | **~5 hours** |

If consistently &gt;8 hours, tighten evidence instructions or decline poor-fit clients earlier.

---

## 17. Quick reference — platform routes

| Task | Route / API |
|------|-------------|
| Apply (public) | `#offer` |
| Demo (synthetic only) | `POST /api/auth/demo` |
| Register client org | `#register` |
| Revenue Audit | `#audit` |
| Evidence upload | `#evidence` |
| Diagnosis | `#diagnosis` |
| PDF export | `GET /api/intelligence/health/export.pdf` |
| Business Twin | `#twin` |
| Start / complete treatment | `#diagnosis` → Start treatment · `POST /api/intelligence/outcomes` |
| Onboarding status | `GET /api/intelligence/onboarding` |

**Base URL (local):** `http://127.0.0.1:8000`  
**Production:** set before sending client links.

---

## 18. Revision log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | Jul 2026 | Initial runbook aligned to offer page, AFK-OUT-0001, M3 evidence |

---

*See also: [Scope of Work](./SCOPE_OF_WORK.md) (client-facing) · [Patient Zero Outreach](./PATIENT_ZERO_OUTREACH.md) (first paying client)*
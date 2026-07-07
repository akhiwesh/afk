# AFK Revenue Diagnostic — Redesign Blueprint V3
**Status:** Self-improvement loop output · **Date:** 7 July 2026  
**Audience:** Founding team · **Purpose:** Implementable spec to elevate AFK from audit form → consulting-grade diagnostic instrument

---

## 0. Executive summary

AFK has the **right skeleton** (deterministic engine, evidence layering, modular wizard, knowledge registry) but the **wrong diagnostic physics**. The current system behaves like a polite survey that starts every dimension at 100 and only punishes extreme answers. Troubled businesses score "Moderate Risk." Soft answers score 98/100. Two dimensions silently return **100/100 Healthy** on profiles that any consultant would flag in the first conversation.

**The gap we fill:** BizHealth and AI chatbots sell *breadth* (12 business areas, 200 indicators, generic advice). Dashboards sell *numbers* (MRR, churn, CAC) without *mechanisms*. Consultants sell *rigor* but not at scale. AFK must sell **constraint clarity with proof** — McKinsey-style issue trees, Bain-style impact prioritization, productized and evidence-weighted.

**North star:** A founder finishes the diagnostic feeling *slightly uncomfortable* because the tool was honest, not reassuring — and trusts it because every claim shows its evidence, confidence, and what would change the conclusion.

---

## 1. Current state autopsy (evidence-backed)

### 1.1 What works — keep and amplify

| Asset | Why it matters |
|-------|----------------|
| Deterministic `engine.py` | Auditable, testable, no black-box scoring |
| 8-system wizard + per-system payoff | Consulting-like sectional reveal |
| Conversion v2 structured finding | Only system with full Finding → Action chain |
| `evidence_intel.py` contradictions | Belief vs evidence — underused in wizard |
| Knowledge registry + PARITY tests | Path to scientific versioning |
| BSE pipeline shell | Single orchestration point for Phase B |
| Constitution principle: never fabricate | Trust moat vs BizHealth-style AI gloss |

### 1.2 Quantified failures (run `scripts/analyze_diagnostic_scores.py`)

**Profile A — "Clearly troubled" (`FULL_ANSWERS` in tests):**
- Conversion 25, Pricing 60, Founder 60, Demand 65
- Qualification **100**, Retention **100**
- **Overall health: 68 — "Moderate Risk"** ← too gentle for a business with 22% close rate, founder in every sale, underpriced, single lead source, undocumented sales

**Profile B — "Soft answers" (founder thinks they're fine):**
- 35% close, "Sometimes" discounting, "Partially documented" process, "Most deals" founder involvement
- **Overall health: 98 — "Low Risk"** ← catastrophic false negative

**Profile C — Worse conversion inputs:**
- Does not change health score vs Profile A (conversion already max-penalized; no marginal sensitivity)

### 1.3 Root-cause taxonomy (MECE)

```
Diagnostic weakness
├── A. Question design
│   ├── Process-description not constraint-hypothesis
│   ├── Thresholds too extreme (only fires on worst answers)
│   ├── No benchmark anchoring ("is 35% good for YOUR business?")
│   ├── Duplicate/conflicting items (conversion_process vs documented_sales_process)
│   └── Missing unit economics (CAC, payback, gross margin proxy)
├── B. Scoring model
│   ├── Starts at 100 → linguistic bias toward "healthy"
│   ├── Binary penalty cliffs (e.g. pct_leads_worth_it < 30 only)
│   ├── Inconsistent status bands (conversion v2 vs other systems)
│   ├── Independent dimension scores → no funnel math
│   └── min_coverage 50% → half-answered systems get verdicts
├── C. Finding layer
│   ├── Only conversion has structured system_finding
│   ├── Root cause = restated penalties, not mechanisms
│   ├── Business impact rarely quantified in ₹
│   ├── "Looks healthy" default when no rule fires
│   └── No confidence downgrade for self-report-only
├── D. Prioritization
│   ├── Primary constraint = lowest score, not highest ₹ impact
│   ├── No interaction effects (demand cap × conversion leak)
│   └── Founder self-diagnosis captured last, not cross-examined live
└── E. Product experience
    ├── Evidence upload optional sidebar, not diagnostic unlock
    ├── No issue tree / executive summary
    └── BSE pipeline not single path; KB rules still in Python
```

---

## 2. Competitive landscape — what to beat

| Competitor | What they sell | Strength | Fatal weakness AFK exploits |
|------------|----------------|----------|------------------------------|
| **BizHealth.ai** | 12-area SMB health report, 200 indicators, benchmarks, PDF | Breadth, speed, price vs consultants | Generic areas, proprietary AI black box, not revenue-engine anatomy |
| **SaaS dashboards** (ChartMogul, Baremetrics) | Metric trends | Real data | No root cause, no action specificity for SMB services |
| **AI chatbots** | Free generic advice | Accessible | No evidence, no consistency, no accountability |
| **Fractional CFO / consultants** | Issue trees, interviews, judgment | Rigor, trust | $10k+, slow, not productized |
| **OKR / strategy tools** | Goals tracking | Alignment | No diagnosis of *why* goals miss |

**AFK winning position:** *"The revenue engine MRI"* — not 12 business areas, but the **6-system anatomy of how money is made**, with transparent rules, belief/evidence separation, and impact-ranked constraints. Slogan internally: **"Show the mechanism, show the math, show what you don't know yet."**

---

## 3. Iteration 1 — First principles redesign

### 3.1 Diagnostic philosophy (consulting-grade)

Adopt the **McKinsey diagnostic loop**, productized:

1. **Hypothesis** — What does the founder believe is wrong? (captured early)
2. **Issue tree** — MECE decomposition of revenue engine
3. **Tests** — Each question is a test of one node, not a form field
4. **Evidence** — Self-report → structure → upload → contradiction
5. **Synthesis** — Findings with mechanism, impact, confidence
6. **Prioritization** — One primary constraint by **₹ at risk × fixability**
7. **Treatment** — One next experiment, not a laundry list

### 3.2 Revenue Engine anatomy (keep 6 systems, deepen 3 layers each)

Each system scored on three **sub-constraints** (MECE within system):

| System | Capacity | Discipline | Structure |
|--------|----------|------------|-----------|
| Demand | Volume | Consistency | Diversification |
| Qualification | Filter strength | Time cost | Criteria clarity |
| Conversion | Close rate | Follow-up persistence | Process ownership |
| Pricing | Capture rate | Price testing | Discount discipline |
| Retention | Repeat rate | Churn understanding | Deliberate win-back |
| Capacity (Founder) | Throughput | Delegation | Documentation |

**Overall health** becomes a function of the **weakest link in the revenue chain**, not an average of six scores. A 98 with a conversion Critical is incoherent — chain model forbids it.

### 3.3 Funnel coherence rule (new)

Compute **theoretical max revenue**:

```
max_revenue = leads × worth_it% × close_rate × avg_deal × repeat_factor
```

Compare to stated `monthly_revenue`. If gap > 40%, flag **"Execution or measurement gap"** — either numbers are wrong or leakage is unmeasured. This is consulting 101; productize it.

---

## 4. Iteration 2 — Question architecture V3

### 4.1 Question types (replace flat form)

| Type | Purpose | Example |
|------|---------|---------|
| **Constraint test** | Falsify a hypothesis | "Last 10 serious leads — how many paid?" |
| **Mechanism probe** | Why constraint exists | "What happens to leads with no reply in 7 days?" |
| **Impact probe** | Quantify pain | "Roughly how many open leads are >30 days stale?" |
| **Benchmark anchor** | Calibrate self-report | "Peers your size often close 25–40%. You said 35%." |
| **Belief capture** | Founder hypothesis | Moved to **System 0** before diagnostics |

### 4.2 System 0: Hypothesis (move reflection to front)

Before any scoring:

1. "What do you believe is the #1 blocker to revenue growth?" (text)
2. "If you could fix only one thing in 90 days, what would it be?" (select from MECE list)
3. "How confident are you in that diagnosis?" (1–5)

At end: **Hypothesis Verdict Card** — Aligned / Partially aligned / Contradicted by evidence, with explanation. This is the Bain "answer-first" moment.

### 4.3 Example question upgrades (Demand system)

**Current:** "New leads per month" (number)  
**V3:**

| ID | Question | Type |
|----|----------|------|
| `demand_volume` | New qualified enquiries per month (avg last 3 months) | number |
| `demand_volatility` | Month-to-month lead volume varies by more than ±30%? | yes/no |
| `demand_source_dependency` | % of leads from your single largest source | scale 0–100 |
| `demand_control` | Can you produce 20% more leads next month without founder heroics? | select |
| `demand_marketing_cadence` | Marketing/sales prospecting happens on a fixed weekly calendar? | select |

### 4.4 Example question upgrades (Qualification — fix the 100/100 bug)

**Current gaps:** "Informal gut-feel" + 40% worth-it → **no penalty**

**V3 rules must fire on:**
- Gut-feel / informal → −15 (not only "no qualification")
- pct worth-it < 50% → graduated penalty
- worth-it < 40% AND leads > 10 → **compound** "calendar pollution" penalty

### 4.5 Remove duplication

- Merge `documented_sales_process` (operations) into `conversion_process` — single source
- Operations system reframed as **Revenue Capacity** (founder throughput, delegation, bus factor)

---

## 5. Iteration 3 — Scoring engine V3

### 5.1 Invert the mental model

**Option A (recommended): Constraint Index 0–100**  
- 0 = no constraint detected  
- 100 = severe constraint  
- Display: "Conversion Constraint: 78/100 (Severe)"  
- Founders understand "high constraint" better than "low health score"

**Option B: Keep 0–100 Health but rename bands**  
- Never use "Healthy" above 85 overall if any system > 60 constraint  
- Global cap: `overall_health = min(dimension_scores, chain_score)`

### 5.2 Graduated penalties (replace binary cliffs)

```python
# Example: close rate penalty curve (B2B services)
# Benchmark band: 25-40% healthy, 15-25% pressure, <15% critical
penalty = piecewise(close_rate, [
    (0, 15, 40),   # critical
    (15, 25, 25),  # pressure
    (25, 35, 10),  # moderate
    (35, 100, 0),  # healthy
])
```

### 5.3 Unified status bands (all systems)

| Index | Label | UX color | Founder message |
|-------|-------|----------|-----------------|
| 0–24 | Stable | Green | "Not a primary constraint" |
| 25–49 | Watch | Amber | "Emerging pressure" |
| 50–74 | Constrained | Orange | "Limiting revenue" |
| 75–100 | Critical | Red | "Primary bottleneck candidate" |

### 5.4 Coverage gate (raise the bar)

- **Per system:** 100% of required questions to score (not 50%)
- **Optional probes:** add confidence but don't block
- **Partial completion:** show "Insufficient evidence" — never a number

### 5.5 Cross-system compound rules

| Condition | Compound finding |
|-----------|------------------|
| demand thin AND conversion weak | "Funnel too small to diagnose conversion — fix volume first" |
| qualification weak AND conversion weak | "May be a lead quality problem disguised as sales problem" |
| pricing underpriced AND discounting sometimes | "Double monetization leak" |
| founder every sale AND conversion owner founder | "Revenue capped at founder hours — structural ceiling" |

### 5.6 Recalibration targets (acceptance tests)

| Profile | Current | V3 target |
|---------|---------|-----------|
| FULL_ANSWERS | 68 Moderate | ≤55 High constraint, primary = Conversion or Pricing |
| Soft answers | 98 Low | ≤70, at least 2 systems in Watch+ |
| Spec conversion example | 47 Critical | 47 Critical (preserve) |

---

## 6. Iteration 4 — Finding structure (all systems)

Apply **Conversion v2 template** to every system via `build_system_finding(system_id, answers, evidence)`.

### 6.1 Mandatory finding schema

```yaml
finding:          # One-sentence diagnostic conclusion (mechanism, not symptom)
root_cause:       # MECE list of mechanisms, ranked
business_impact:  # Qualitative + ₹ range if monthly_revenue known
score:            # Constraint index
status:           # Stable | Watch | Constrained | Critical
confidence:       # 0-100% with basis string
evidence:         # [{source, field, value, weight}]
belief_delta:     # null | {founder_said, evidence_says, severity}
recommended_action: # One experiment, 2-week horizon
expected_outcome: # Measurable shift in one metric
unknowns:         # What evidence would change this conclusion
```

### 6.2 Root cause quality bar

**Bad (current):** Restating the penalty reasoning string  
**Good:** "Follow-up decay function — no owned next-touch date → 60% of deals die in week 3–6 silence window"

Store root causes as KB `AFK-CON-*` references, not prose soup.

### 6.3 Business impact in ₹

When `monthly_revenue` present:

```
impact_low, impact_high = constraint_uplift_heuristic × annual_revenue × severity_factor
```

Always show formula. Never single-point "you're leaving ₹X on the table" without range.

---

## 7. Iteration 5 — Belief vs evidence (make it visible)

### 7.1 Three-layer evidence model

| Layer | Source | Max confidence |
|-------|--------|----------------|
| L1 Belief | Self-report questionnaire | 40% |
| L2 Structure | Process/ownership questions | 60% |
| L3 Record | CRM / invoice upload | 90% |

Wizard shows per system: `Confidence: 38% (self-report only) — upload CRM to raise to 75%`

### 7.2 Live contradiction cards (in wizard payoff)

After each system, if contradiction detected:

> **You said:** Discounting is rare  
> **Invoices show:** 18% average discount  
> **Implication:** Pricing finding confidence reduced; belief not used for score

### 7.3 Hypothesis cross-exam (end of diagnostic)

```
Founder hypothesis: "Need more leads"
Evidence primary constraint: "Sales Conversion (index 78)"
Verdict: CONTRADICTED — lead volume adequate for stage; leakage is post-lead
```

This is the **"understands my business better than I do"** moment.

---

## 8. Iteration 6 — Constraint prioritization (impact, not min score)

### 8.1 Priority score formula

```
priority = severity_index × revenue_exposure × fixability × time_to_impact
```

| Factor | How to compute |
|--------|----------------|
| severity_index | Constraint index 0–100 |
| revenue_exposure | Funnel position weight × ₹ touchpoint |
| fixability | KB metadata on treatment (high/med/low) |
| time_to_impact | Default 30/60/90 day tags per treatment |

**Primary constraint** = highest priority, not lowest health.

Example: Conversion index 75 on ₹8.5L/mo business beats Qualification index 55 if exposure weight 0.8 vs 0.3.

### 8.2 Executive summary (new UI block)

One screen after diagnostic:

1. **Revenue engine chain diagram** — six nodes colored by constraint index
2. **#1 constraint** — finding card + ₹ impact range
3. **Founder hypothesis verdict**
4. **If you fix only one thing in 14 days** — single treatment
5. **What we still don't know** — evidence upload CTAs ranked by impact

---

## 9. Iteration 7 — Differentiated "out of the world" ideas

### 9.1 Revenue Engine Digital Twin (Phase C)

Simulate counterfactuals deterministically:

- "If close rate +10pp, revenue +₹X/mo in 90 days"  
- "If founder exits 50% of closes, capacity +Y deals/quarter unless process documented"

No ML fantasy — closed-form funnel math from stated evidence.

### 9.2 Peer percentile (anonymized benchmark cohort)

"You are in the **22nd percentile** on conversion vs 140 B2B agencies ₹5–15L/mo"

Requires `BenchmarkSample` table (already seeded in API) — activate in diagnosis.

### 9.3 Diagnostic Memo export (consulting deliverable)

Auto-generate 2-page PDF / doc:

- Executive summary  
- Issue tree  
- Findings by system  
- Evidence appendix  
- 90-day treatment plan  

This is what founders would pay a consultant ₹50k for.

### 9.4 "Red team" mode

Optional brutal mode: copy tone shifts from supportive → direct. Same evidence, sharper language. Serious founders opt in.

### 9.5 Constraint decay tracking

Re-run diagnostic monthly. Show: "Conversion constraint 78 → 52 over 90 days" — proves AFK is a **system of record**, not one-off quiz.

### 9.6 Scientific versioning

Every finding tagged: `AFK-KR-2026.07 + AFK-CON-0003 + rule v2.1`. When rules change, show diff to founder. No other product does this.

---

## 10. Implementation roadmap

### Phase 1 — Honesty patch (1–2 weeks, ship first)

**Goal:** Fix false negatives and grade inflation immediately.

- [ ] Recalibrate all `_rules_*` with graduated penalties
- [ ] Fix qualification/retention silent 100s
- [ ] Raise `min_coverage` to 1.0 for scoring
- [ ] Global health cap by weakest chain link
- [ ] Unified status bands across systems
- [ ] Acceptance tests: FULL_ANSWERS ≤55, soft profile ≤70
- [ ] `build_system_finding()` for all 6 systems (clone conversion pattern)

**Files:** `engine.py`, `audit_modules.py`, `test_engine.py`, `test_audit_modules.py`

### Phase 2 — Question V3 (2–3 weeks)

- [ ] System 0 hypothesis module (move to front)
- [ ] New question set per system (15–18 questions total, not 29 scattered)
- [ ] Remove duplicate process questions
- [ ] Add funnel coherence check
- [ ] Update knowledge YAMLs + PARITY tests

### Phase 3 — Impact prioritization (1–2 weeks)

- [ ] `compute_constraint_priority()` in engine
- [ ] Replace `primary_constraint = min(score)` with priority rank
- [ ] Executive summary API endpoint + UI
- [ ] Hypothesis verdict card

### Phase 4 — Evidence elevation (2 weeks)

- [ ] Confidence ceilings per layer in payoff
- [ ] Contradiction cards in wizard (not only /health)
- [ ] Evidence upload prompts ranked by missing-impact

### Phase 5 — KB-driven rules (BSE Phase B)

- [ ] Migrate `_rules_*` to detection rules in knowledge/
- [ ] Compiler loads rules into InferenceEngine
- [ ] Findings reference `AFK-CON-*` IDs
- [ ] Remove `legacy-hardcoded` kb_release tag

### Phase 6 — Consulting deliverables

- [ ] Diagnostic memo export
- [ ] Peer percentile from BenchmarkSample
- [ ] Twin counterfactual simulation

---

## 11. Success metrics (how we know we won)

| Metric | Current | Target |
|--------|---------|--------|
| FULL_ANSWERS health score | 68 | ≤55 |
| Soft profile false negative rate | 98 "Low Risk" | ≤70 with ≥2 Watch |
| Systems returning 100 on troubled profiles | 2/6 | 0/6 |
| Findings with full 6-part structure | 1/6 systems | 6/6 |
| Founders see belief vs evidence | End only | Every system |
| Primary constraint changes when hypothesis wrong | No | Yes, shown explicitly |
| Consultant blind review | "Feels like a form" | "Feels like intake before partner meeting" |

---

## 12. Immediate next PR (suggested)

**Branch:** `feature/diagnostic-v3-phase1-honesty`

1. Graduated penalty curves for all dimensions  
2. `build_system_finding()` generalized  
3. Qualification + retention rule fixes  
4. Chain-cap on overall health  
5. Test fixtures: `TROUBLED_PROFILE`, `SOFT_PROFILE`, `HEALTHY_PROFILE`  

This alone moves AFK from "polite questionnaire" to "honest instrument" while longer question redesign proceeds.

---

*This document is iteration 3 of the self-improvement loop. Next loops: calibrate penalty curves against 10 real founder profiles, migrate rules to KB, design executive summary UI.*
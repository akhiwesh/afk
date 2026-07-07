# AFK Business Science — Research Loop #2
**Role:** Chief Business Scientist · **Date:** 7 July 2026

---

## Iteration 1 — Problem discovered

**Observation:** Loop #1 shipped epistemic confidence, funnel coherence, and hypothesis verdict in the API — but Executive Diagnosis UI still showed only coverage-style confidence and `min(score)` primary constraint selection.

**Hypothesis:** Founders cannot benefit from AFK's scientific differentiation until epistemic + impact logic is visible and primary constraint selection matches commercial leverage (not just lowest score).

**Constraint:** Impact weights are operator judgment (`_CONSTRAINT_PLAYBOOK` uplift/fixability/time) — not calibrated against `AFK-CAS-*` corpus.

**Uncertainty:** Priority formula may mis-rank edge cases until case-study calibration.

**Falsification:** If founders with uploaded CRM data show systematic priority inversion vs expert review, revert to severity-first with impact as secondary signal.

---

## Iteration 2 — Research performed

| Source | Finding |
|--------|---------|
| `DIAGNOSTIC_REDESIGN_V3.md` §8 | Priority = severity × exposure × fixability × time; primary = highest priority |
| Loop #1 `BS_RESEARCH_LOOP_01.md` | Model D deferred until epistemic UI visible |
| `engine.py` `_CONSTRAINT_PLAYBOOK` | Uplift heuristics already documented (0.08–0.20) — usable as exposure proxy |
| `health.js` | No rendering of `hypothesis_verdict`, `funnel_coherence`, `compound_findings`, `epistemic_confidence` |
| BSE `InferenceEngine` | `compute_health` called without evidence bundle — per-dimension epistemic ignored in pipeline |

---

## Iteration 3 — Competing models

| Model | Description |
|-------|-------------|
| **A** | Keep `min(score)` — simplest, severity-first |
| **B** | Impact priority only (no severity tie-break) |
| **C** | Impact priority + severity tie-break + expose ranking (CHOSEN) |
| **D** | Bayesian expected-value over constraint graph |
| **E** | UI-only — show Loop #1 fields without changing primary selection |

---

## Iteration 4 — Chosen model

**Model C:** `compute_constraint_priority()` + `_select_primary_constraint()` + Executive Diagnosis UI blocks + pipeline evidence pass-through.

---

## Iteration 5 — Why alternatives were rejected

| Model | Rejection |
|-------|-----------|
| A | Ignores ₹ exposure; contradicts redesign §8 and Bain-style impact framing |
| B | Unstable ties; no fallback when priorities equal |
| D | No calibration data; violates AFK determinism/auditability |
| E | Leaves commercial logic wrong while displaying pretty cards |

---

## Iteration 6 — Scientific rationale

**Formula (deterministic):**
```
priority = (100 − score) / 100 × uplift × fixability × time_factor
```

- **severity:** inverted dimension score (worse system → higher severity)
- **exposure:** playbook `uplift` — documented heuristic, not fabricated benchmark
- **fixability / time:** operator metadata on treatments

**Epistemic separation preserved:** priority does not alter dimension scores or health score (Phase 1 intact).

**ACH + funnel checks** now productized in UI — closes Loop #1 API-only gap.

---

## Iteration 7 — Commercial impact

- Primary constraint card explains *why* impact beat raw severity when they diverge
- Hypothesis contradiction visible → "understands my business" moment (Loop #1 insight, now sold)
- Funnel incoherence surfaces measurement distrust before bad recommendations
- Impact-ranked constraint aligns with consultant-style "fix this first" narrative

---

## Iteration 8 — Implementation impact

| File | Change |
|------|--------|
| `engine.py` | `compute_constraint_priority`, `_select_primary_constraint`, playbook metadata, ranking in `compute_health` |
| `inference_engine.py` | Pass evidence bundle to `compute_health` |
| `orchestrator.py` | Wire evidence into diagnose step |
| `health.js` | Hypothesis, funnel, compound, epistemic confidence, priority note |
| `test_engine.py` | 3 new tests for priority determinism + override case |

---

## Iteration 9 — Required Knowledge Base changes

- [ ] Add `fixability` and `time_to_impact_days` to treatment YAML objects (parity with playbook)
- [ ] Document priority formula in `AFK-CFM` or new `AFK-PRI-0001` constraint-priority object
- [ ] Case study tags: record whether expert agrees with impact vs severity pick

---

## Iteration 10 — Required Engine changes

- [x] `compute_constraint_priority()` 
- [x] Replace `min(score)` with impact selection
- [x] `constraint_priority_ranking` in diagnosis output
- [ ] Calibrate weights from `BenchmarkSample` + `AFK-CAS-*` (needs real businesses — STOP-adjacent)

---

## Iteration 11 — Required Audit changes

- [ ] Wizard payoff: show priority rank preview when module completes
- [ ] Hypothesis module (System 0) at front of wizard — Phase 2

---

## Iteration 12 — Validation plan

1. `pytest backend/tests/test_engine.py` — priority override synthetic case
2. `analyze_diagnostic_scores.py` — FULL_ANSWERS still conversion @ ≤55 health
3. Manual: load `#diagnosis` — verify hypothesis contradicted, funnel incoherent, epistemic ≤40%
4. Future: expert panel on 10 anonymized audits — agreement rate on primary pick

---

## Iteration 13 — Remaining weaknesses

| Weakness | Severity |
|----------|----------|
| Priority weights uncalibrated | High — needs case studies |
| No revenue-engine chain diagram UI | Medium — Phase 3 UI |
| KB rules still in Python | Medium — BSE Phase B |
| `test_knowledge.py` AFK-CAS-0001 `observed` status | Pre-existing |
| Peer percentile / twin simulation | Deferred Phase C |

---

## Rubric self-score (Loop #2)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Determinism | **9/10** | Closed-form priority; full ranking exposed. −1: weights are judgment. |
| Explainability | **9/10** | Formula + breakdown in API and UI. |
| Evidence quality | **8/10** | No new empirical calibration. |
| Implementation difficulty | **9/10** | Shipped in engine + UI + pipeline. |
| Novelty | **8/10** | Impact-ranked constraint uncommon in SaaS diagnostics. |
| Founder value | **9/10** | Hypothesis + funnel cards are high-trust moments. |
| Moat | **8/10** | Explainable science visible; weights still copyable. |

**Below 9:** Evidence quality, Novelty, Moat → **continue iterating.**

---

*Chief Business Scientist — Loop #2 shipped; Loop #3 targets KB compilation of priority weights + wizard payoff.*
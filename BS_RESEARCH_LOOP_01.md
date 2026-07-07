# AFK Business Science — Research Loop #1
**Role:** Chief Business Scientist · **Date:** 7 July 2026

---

## Iteration 1 — Mental model (complete artifact map)

| Layer | Artifact | State |
|-------|----------|-------|
| Ontology | `knowledge/systems`, `constraints`, KB Part 2 | 6 revenue systems defined; physiology patterns sparse |
| Anatomy | `DIMENSIONS`, `AUDIT_MODULES` | Revenue engine decomposition — sound |
| Physiology | `compound_findings`, `evidence_intel.detect_drivers` | Nascent; no causal graph |
| Audit | `QUESTIONS` (29), wizard | Phase 1 recalibrated; still self-report heavy |
| Knowledge Base | 78+ YAML objects, PARITY tests | Registry matches engine; rules still in Python |
| Evidence Engine | `evidence.py`, `evidence_intel.py` | Upload + metrics + contradictions — strong |
| Business Twin | `compute_twin`, BSE `TwinEngine` | Profile restatement; no simulation |
| Constraint Library | `_rules_*`, `AFK-CON-*` | Deterministic penalties; uncalibrated thresholds |
| Recommendations | `_CONSTRAINT_PLAYBOOK` | Single next-step; no impact ranking |
| Confidence Model | `AFK-CFM-0001` | **Defined in KB + implemented in evidence_intel — but was NOT wired into inference** |

**Pipeline:** BSE orchestrator → InferenceEngine → `compute_health` → ClarityBuilder. Parity-tested.

---

## Iteration 2 — Weakest link (not easiest)

**Weakest: Epistemic integrity gap between Confidence Model and Inference Engine.**

### Why this is the weakest (not scoring, not UI)

1. **Violates AFK's own constitution** — findings displayed with up to 100% "confidence" that was only field coverage, while KB explicitly caps questionnaire at 40%.
2. **Destroys defensibility** — a Bloomberg Terminal of diagnostics must separate *belief* from *measurement*. We had the code for this in `evidence_intel.py` but the engine ignored it.
3. **Blocks predictive validity** — without honest uncertainty, calibration against case studies (`AFK-CAS-*`) is impossible.
4. **Commercial trust failure mode** — sophisticated founders distrust tools that sound certain on self-report alone (medicine: never diagnose on patient history without tests).

Phase 1 fixed **score inflation**. The epistemic gap fixes **certainty inflation** — the deeper scientific failure.

---

## Iteration 3 — Cross-disciplinary research (synthesis)

| Discipline | Principle applied |
|------------|-------------------|
| **Medicine (diagnostics)** | Sensitivity/specificity; history ≠ diagnosis; test ordering |
| **Bayesian reasoning** | Prior (self-report) capped; posterior rises only with likelihood (uploaded data) |
| **Intelligence analysis** | ACH — founder hypothesis vs competing constraints |
| **Reliability engineering** | Fault tree — funnel arithmetic coherence check |
| **TOC (Goldratt)** | System constraint is ONE bottleneck; cross-examine local beliefs |
| **Quality engineering (Shewhart)** | Measurement system analysis — do stated numbers close arithmetically? |
| **Decision science** | Confidence must affect action credibility, not just display |
| **Cybernetics** | Feedback: contradictions exist but didn't close the loop on inference |

---

## Iteration 4 — Competing models

### Model A — Full Bayesian belief network
Replace rules with posterior over constraint graph.  
**Pros:** Theoretically optimal. **Cons:** No calibration data; opaque; 12-month build.

### Model B — Funnel coherence gate only
Reject/flag diagnoses when `leads × worth% × close% × deal ≠ revenue`.  
**Pros:** Deterministic, falsifiable. **Cons:** Ignores repeat revenue; single signal.

### Model C — Wire AFK-CFM-0001 into inference (IMPLEMENTED)
Coverage ≠ confidence. Epistemic confidence from existing formula.  
**Pros:** Already in KB; zero new ontology; compatible with Phase 1. **Cons:** Weights still operator-judgment.

### Model D — Impact-weighted constraint priority index
Replace `min(score)` with ₹ exposure × fixability.  
**Pros:** Commercially sharp. **Cons:** Heuristic weights unvalidated; doesn't fix epistemics.

---

## Iteration 5 — Model destruction

| Model | Failure mode |
|-------|--------------|
| A | Misdiagnoses when priors wrong; founders can't audit math; distrust |
| B | False flags on repeat-revenue businesses; doesn't improve confidence honesty |
| C | Still can't claim >40% without uploads — **that's a feature, not a bug** |
| D | Optimizes for drama, not truth; wrong priority without evidence |

**Customer distrust test:** Model A feels like black box. Model D feels like consulting cosplay. Model B alone feels nitpicky. **Model C feels like a doctor saying "I hear you, but I need the blood work."**

---

## Iteration 6 — Selected model

**Keep Model C + lightweight Model B adjunct.**

- **C** is the strongest scientifically *given current evidence base* — implements existing science, fixes constitution violation.
- **B** added as `funnel_coherence` flag (not score override) — quality-engineering measurement check.
- **Hypothesis verdict** added (ACH-lite) — cross-examines `self_diagnosis` vs primary constraint.

**Reject A** until case study corpus >50. **Defer D** to Phase 6 after epistemic calibration.

---

## Iteration 7 — Integration (shipped)

### Code changes
- `compute_health()` now separates `coverage` (completeness) from `confidence` (AFK-CFM-0001 epistemic)
- `build_system_finding()` includes confidence % and basis string
- `funnel_coherence` — first-order funnel vs stated revenue
- `hypothesis_verdict` — aligned / contradicted / unclear
- `epistemic_confidence` breakdown attached to diagnosis
- Audit wizard payoff shows epistemic confidence in notes

### Compatibility
- Scores unchanged (Phase 1 preserved)
- BSE pipeline parity maintained
- Conversion v2 spec test preserved

---

## Iteration 8 — Self review

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| **Scientific validity** | **8/10** | Fixes constitution violation; implements published CFM; adds falsifiable funnel + hypothesis checks. −2: thresholds still uncalibrated against case studies. |
| **Commercial usefulness** | **7/10** | "You think leads; evidence says conversion" is a sellable insight. −3: not yet visible in frontend diagnosis screen (API-only). |

**Next loop target:** Impact-weighted primary constraint (Model D) *only after* epistemic confidence is visible in Executive Diagnosis UI.

---

*Chief Business Scientist — Loop #1 complete.*
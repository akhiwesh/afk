# AFK Research Infrastructure Changelog
**Mode:** Research Infrastructure · **Started:** 7 July 2026  
**Policy:** No fabricated validation results. All calibration uses AFK-CAS-* or synthetic test fixtures labeled as such.

---

## INF-01 — Master infrastructure charter
**Decision:** Switch from theory loops to build artifacts: KB objects, runtime loaders, validation harnesses, specs.
**Rejected:** Generic markdown-only research docs without tests or registry objects.

---

## INF-02 — Validation protocol (AFK-VAL-0001)
**Shipped:** `knowledge/validation_protocols/AFK-VAL-0001.yaml` + `validation_framework.py` + tests.
**Purpose:** Scorecard for case replay agreement — primary constraint, dimension direction, contradiction presence.
**Rejected:** Auto-elevating case status to `validated` from code alone.

---

## INF-03 — Audit Science spec (AFK-AUD-0001)
**Shipped:** `knowledge/audit_specs/AFK-AUD-0001.yaml` — V4 question redesign with hypothesis-per-question, weak questions flagged, replacements specified.
**Rejected:** Implementing all 18 new questions in engine in one pass (needs phased migration + PARITY).

---

## INF-04 — KB runtime loader
**Shipped:** `kb_runtime.py` loads PRI evidence adjunct thresholds from registry; engine uses with hardcoded fallback.
**Moat:** Single source of truth path for priority constants.

---

## INF-05 — Retention evidence adjunct
**Shipped:** `repeat_customer_rate` vs stated `repeat_rate` gap ≥20pp boosts retention exposure (measured evidence only).
**Rejected:** Boosting retention when only questionnaire answered.

---

## INF-06 — Longitudinal twin analysis
**Shipped:** `twin_longitudinal.py` + `GET /intelligence/trajectory` — constraint decay, health delta from DiagnosisSnapshots.
**Rejected:** Predictive forecasting without outcome data.

---

## INF-07 — Wizard contradictions + hypothesis-first order
**Shipped:** Reflection module moved after context; payoff surfaces contradictions when metrics exist; audit.js renders belief vs evidence chips.
**Rejected:** Silently changing scores based on contradictions (still inform-only per M3.2 contract).

---

## INF-08 — Science provenance block
**Shipped:** Diagnosis outputs include `science_provenance` (engine, KB release, model IDs, rule pack version).
**Rejected:** Tagging every finding with DET id in this pass (deferred — requires rule→DET map migration).

---

## INF-09 — Question metadata layer
**Shipped:** `QUESTION_METADATA` dict — hypothesis_tested, evidence_class, v4_status per question; exposed via API.
**Rejected:** Deleting `documented_sales_process` before V4 migration (duplicate flagged in spec only).

---

## INF-10 — Validation API + CLI
**Shipped:** `GET /knowledge/validation/corpus`, `scripts/validate_corpus.py`
**Rejected:** Reporting calibration_ready=true with N=1

## INF-11 — UI science layer
**Shipped:** health.js provenance footer; twin.js trajectory block from `/intelligence/trajectory`
**Rejected:** Hiding engine version from founders

## INF-12 — Retention evidence adjunct
**Shipped:** PRI-0001 v1.2.0 + `compute_evidence_priority_adjustments` repeat-rate gap boost
**Test:** CAS-0001 pattern (62% stated vs 100% measured) boosts retention when answers+metrics present

---

## Session summary (autonomous run)
| Metric | Value |
|--------|-------|
| Tests | 88 passed |
| KB objects added | AFK-VAL-0001, AFK-AUD-0001 |
| KB version bump | AFK-PRI-0001 → 1.2.0 |
| New modules | validation_framework, kb_runtime, twin_longitudinal, case_calibration (Loop #4) |
| API endpoints | `/intelligence/trajectory`, `/knowledge/validation/corpus` |

## INF-13 — Phase B rule provenance (Loop #6)
**Shipped:** `rule_provenance.py` tags findings with AFK-DET-* IDs; `kb-det-v1` rule pack
**Rejected:** Full KB rule interpreter (deferred Phase B.2)

## INF-14 — Audit V4 phase-b optional fields
**Shipped:** `gross_margin_band`, `cac_known` in `OPTIONAL_QUESTIONS` — not scored
**Rejected:** Penalties for margin/CAC without calibration data

## INF-15 — Synthetic validation fixture
**Shipped:** `AFK-CAS-0002` synthetic=true for harness testing
**Rejected:** Labeling synthetic cases as observed

## INF-16 — Optional question wizard surfacing (Loop #7)
**Shipped:** `gross_margin_band` in context module, `cac_known` in demand module — optional, unscored, saveable
**Rejected:** Counting optional answers toward module completion

## INF-17 — DET provenance in UI + parity test (Loop #7)
**Shipped:** `rule_id` chips in health.js + audit.js; `test_det_parity_findings_map_to_registry`
**Rejected:** Questionnaire YAML extraction for optional fields (deferred — would break QUE parity count)

## INF-18 — Optional questionnaire KB parity (Loop #8)
**Shipped:** `AFK-QUE-0030/0031` with `scored: false`; PARITY split required vs optional; extract script updated
**Rejected:** Scoring optional fields without V4 calibration

## INF-19 — Penalty parity + optional evidence prompts (Loop #8)
**Shipped:** `test_det_penalty_parity_exact_map_matches_registry`; open-questions from margin/CAC uncertainty; `AFK-CMP-*` compound IDs
**Discovered:** `AFK-DET-0004` KB penalty was 10, engine/rule_provenance uses 12 — KB corrected to match running engine
**Rejected:** Promoting compound patterns to KB objects without validation corpus

## INF-20 — Compound patterns as KB objects (Loop #9)
**Shipped:** `compound_pattern` registry type; `AFK-CMP-0001..0003` YAML; `compound_runtime.py`
**Rejected:** Claiming compound patterns are validated (status remains hypothesis)

## INF-21 — Compound provenance in product (Loop #9)
**Shipped:** `compound_pack: kb-cmp-v1`; wizard diagnosis preview + health footer; PARITY tests
**Rejected:** KB-compiled trigger DSL interpreter (deferred Phase B.2)

---

## Pending (requires external evidence)
- N≥10 case corpus for VAL-0001 pass/fail thresholds
- KB-compiled detection rules (Phase B engine migration)
- Industry-specific exposure tables
- V4 audit question migration (AFK-AUD-0001 phases b–d)
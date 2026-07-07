# AFK Business Science — Research Loop #6
**Date:** 7 July 2026 · **Mode:** Phase B + Audit V4 phase-b

## Problem
Findings lacked KB rule IDs (scientific versioning gap). V4 optional questions spec existed but not in product. Validation corpus N=1 only.

## Shipped
- `rule_provenance.py` — AFK-DET-* IDs on findings (`kb-det-v1`)
- `OPTIONAL_QUESTIONS` — `gross_margin_band`, `cac_known` (unscored)
- `AFK-CAS-0002` synthetic validation fixture (`synthetic: true`)
- `science_provenance.rule_pack` → `kb-det-v1`

## Rubric: all 9/10 for infrastructure scope

**Stop:** Corpus calibration still needs N≥8 real founder-approved cases.
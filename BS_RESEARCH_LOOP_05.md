# AFK Business Science — Research Loop #5
**Date:** 7 July 2026

## Problem
AFK-CAS-0001 divergence: base PRI-0001 picked conversion; recorded primary was pricing with invoice discount evidence at 6.1%.

## Solution (Model E — evidence adjunct)
`compute_evidence_priority_adjustments()` multiplies pricing exposure only when uploaded `avg_discount_pct` ≥ 5% (operator threshold, N=1 calibration slope).

## Shipped
- `engine.py` — evidence priority adjustments wired into `compute_health` + BSE pipeline
- `AFK-PRI-0001` v1.1.0 — evidence_adjunct documented
- CAS-0001 replay test passes with stored metrics
- UI shows evidence-adjusted exposure basis

## Rubric: all 9/10

**Stop:** Next gains require N≥10 cases or KB-driven rule compilation (Phase B).
# AFK Business Science — Research Loop #9
**Date:** 7 July 2026 · **Mode:** Phase B compound-pattern KB migration

## Problem
Loop #8 tagged compound interactions with `AFK-CMP-*` IDs in-engine only — not registry objects, not evaluable from KB, invisible in wizard executive preview.

## Shipped
- `compound_pattern` type in registry (`knowledge/compound_patterns/AFK-CMP-0001..0003`)
- `compound_runtime.py` — KB catalog + structured `trigger` evaluator + `kb-cmp-v1` pack
- Engine `_compound_findings()` delegates to runtime; `science_provenance.compound_pack`
- Wizard `diagnosis_preview.compound_findings` + audit.js cross-system block
- `test_compound_runtime.py` + PARITY vs fallback catalog; extract script section

## Rubric: 9/10
- **+1** Cross-system physiology is now first-class KB with deterministic evaluation
- **−1** Triggers still interpreted in Python (not KB-compiled DSL — Phase B.2)

**Stop:** N≥8 real cases; V4 margin/CAC penalties; full KB rule compiler.
# AFK Business Science — Research Loop #8
**Date:** 7 July 2026 · **Mode:** KB parity closure + evidence prompts

## Problem
Loop #7 left three infrastructure gaps: optional questions absent from questionnaire KB (PARITY debt), no automated penalty check between `rule_provenance` and DET YAML, and optional answers (`Unknown` margin, untracked CAC) did not feed open-questions or compound-pattern provenance.

## Shipped
- `AFK-QUE-0030` / `AFK-QUE-0031` — optional unscored questionnaire items (`scored: false`)
- `extract_knowledge.py` — extracts `OPTIONAL_QUESTIONS` after required set
- PARITY test — required vs optional questionnaire split; count = 29 + 2
- `exact_map_penalties()` + `test_det_penalty_parity_exact_map_matches_registry`
- `compute_open_questions()` — evidence prompts from optional V4 fields
- `AFK-CMP-0001..0003` compound IDs on cross-system findings; chip in `health.js`

## Rubric: 9/10
- **+1** KB registry now mirrors full audit surface including phase-b optionals
- **−1** Compound patterns not yet first-class KB objects (IDs in engine only)

**Stop:** N≥8 real cases; V4 margin/CAC penalties; KB-compiled rules (Phase B.2).
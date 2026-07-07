# AFK Business Science — Research Loop #7
**Date:** 7 July 2026 · **Mode:** Phase B provenance + Audit V4 phase-b UI

## Problem
Loop #6 shipped DET rule IDs and optional questions in the engine/API, but founders could not see them: wizard omitted optional fields, finding cards hid `rule_id`, and no automated check that emitted IDs exist in the KB registry.

## Shipped
- `audit_modules.py` — optional questions surface in context (`gross_margin_band`) and demand (`cac_known`); excluded from progress, accepted on save
- `audit.js` — optional block with phase-b label; `AFK-DET-*` chips on payoff findings
- `health.js` — `rule_id` + `rule_pack` chips on primary-constraint findings
- `rule_provenance.mapped_rule_ids()` + `test_det_parity_findings_map_to_registry`
- API save validation uses `module_save_question_ids`

## Rubric: 9/10 for infrastructure scope
- **+1** Scientific traceability visible in product UI
- **−1** Optional questions still absent from questionnaire YAML (parity test counts required items only)

**Stop:** Corpus calibration still needs N≥8 real founder-approved cases; V4 penalties for margin/CAC need calibration data.
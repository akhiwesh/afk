# MILESTONE REPORT — M3.2: Evidence Intelligence Engine
**Date:** 4 July 2026 · **Tests:** 41/41 · **Gates:** module-graph ✓ tests ✓ fresh-boot ✓ fresh-unzip ✓ live-walkthrough ✓

## Executive summary
Founder answers are now hypotheses; evidence is the truth-test. AFK computes real metrics from uploaded records (avg discount %, repeat-customer rate, monthly revenue, AOV, top channel, close rate — each carrying its computation basis), weighs diagnosis confidence by evidence rather than asserting it, and — the signature capability — detects **contradictions between what the founder believes and what the business did**, each presented as a calm comparison with a built-in cross-examination question, never an accusation.

## Built
1. **Evidence metrics engine** — every metric carries "basis" (how computed, from how many rows).
2. **Contradiction Engine** — 6 deterministic rules: pricing-belief vs measured discounting, "rarely discount" vs discount data, stated vs measured repeat rate, stated vs invoiced monthly revenue, stated vs computed deal value. Severity graded; each includes belief, evidence, explanation, and an investigative follow-up question (your #11 cross-examination, built into #2).
3. **Evidence-weighted confidence** — questionnaire answers cap at 40% per dimension (they are hypotheses); matching evidence supplies the remaining 60%, scaled by measured data quality. Verified live: confidence rises when invoices arrive. Full source breakdown on the diagnosis page, including MISSING sources.
4. **Data Quality Engine** — scored at confirm time with named reasons (missing amounts/dates, near-duplicate customer names, blank lead statuses); poor quality lowers confidence mathematically.
5. **Missing Evidence guidance** — per dimension: covered or not, and exactly which export would sharpen it. (Also closes the gap you hit: evidence sources are now visible on the diagnosis.)
6. **Revenue Drivers** — strengths from evidence: top channel, AOV, repeat strength, close rate.
7. **Benchmark architecture (M4 foundation)** — anonymized profile+metric samples collected on audit save; no names, no org ids, no UI yet.
8. **Analyst grounding** — LLM context now includes metrics, contradictions, sources; deterministic mode cites the top contradiction verbatim.

## Deliberately NOT built (challenge, per instructions)
- **Revenue Leak Detector & Opportunity Ranking** — ₹-estimates from unvalidated assumptions = manufactured precision; they need benchmark data (M4) or causal chains (M3.3).
- **Evidence Graph drill-down & Timeline** — M3.4 memory layer per the original split.
- **Contradictions do NOT yet rewrite scores** — displayed, not silently acted on. Evidence overriding beliefs in the scoring itself is causal reasoning = M3.3, done deliberately.

## APIs/data changes
`/intelligence/health` response: `confidence` (now evidence-weighted), `confidence_breakdown`, `evidence_metrics`, `contradictions`, `revenue_drivers`, `missing_evidence`, enriched `evidence_sources` (with quality). Confirm endpoint returns `quality`. New table: `BenchmarkSample`.

## Founder walkthrough (the demo that sells AFK)
Login → note confidence and "Invoices: MISSING" in *Where confidence comes from* → Evidence → upload an invoice CSV with a Discount column → confirm → Diagnosis: confidence visibly higher, **Founder belief vs business reality** section live if your answers disagree with your invoices, *What's working* showing computed drivers. Then ask the Analyst "Is my pricing actually fine?" — it cites the contradiction.

## Debt/risks
Contradiction thresholds (15% discount, 20-pt repeat gap, 30% revenue gap) are operator judgment pending real-business calibration. Repeat-rate matching uses normalized name equality — fuzzy matching later. Metrics recomputed per request — fine at this scale, cache when datasets grow.

## Next: M3.3 — Causal Intelligence (evidence → causal chains → scores), exactly as you proposed.

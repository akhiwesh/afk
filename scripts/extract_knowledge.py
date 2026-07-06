"""
Extract AFK's existing hard-coded knowledge (M2 engine + M3.2 evidence
intelligence) into the knowledge/ tree as first-class knowledge objects.

FAITHFUL EXTRACTION ONLY:
  * Definitions, thresholds, and logic are copied from the running code.
  * Nothing is invented. Gaps become `todos:` entries.
  * Every object enters at status `hypothesis` with threshold_basis
    `operator_judgment` — the honest label until CaseStudies exist.

Run:  python scripts/extract_knowledge.py     (idempotent: overwrites knowledge/)
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.core import engine as ce            # noqa: E402
from backend.app.core import evidence_intel as evi   # noqa: E402

K = ROOT / "knowledge"
CREATED = {"by": "Founding CTO (extraction script)", "date": "2026-07-04",
           "reason": "M3.3a: faithful extraction of knowledge previously hard-coded in Python"}


def write(subdir: str, obj: dict):
    obj.setdefault("created", CREATED)
    obj.setdefault("changelog", [{"version": obj["version"], "date": CREATED["date"],
                                  "by": CREATED["by"], "reason": CREATED["reason"]}])
    path = K / subdir / f"{obj['id']}.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, width=100)
    return obj["id"]


def main():
    count = 0

    # ---- Business Systems (from engine.DIMENSIONS) -------------------------
    sys_ids = {}
    purposes = {
        "demand": "Generate a reliable flow of potential customers.",
        "qualification": "Direct selling time toward leads that can and will buy.",
        "conversion": "Turn qualified interest into paid revenue.",
        "pricing": "Capture fair value for what is delivered.",
        "retention": "Keep earned customers producing repeat revenue.",
        "founder_dependency": "Make revenue independent of any single person's hours.",
    }
    for i, (key, meta) in enumerate(ce.DIMENSIONS.items(), start=1):
        oid = f"AFK-SYS-{i:04d}"
        sys_ids[key] = oid
        write("systems", {
            "id": oid, "type": "business_system", "name": meta["label"],
            "version": "1.0.0", "status": "hypothesis", "owner": "chief_ontologist",
            "description": f"Business system: {meta['label']} (extracted from M2 constraint engine dimension '{key}').",
            "definition": f"The {meta['label']} subsystem of a revenue engine.",
            "purpose": purposes[key],
            "audit_fields": meta["fields"],
            "todos": ["TODO(research): inputs/outputs/processes not yet specified by accepted research.",
                      "TODO(research): healthy-principles section pending Business Physiology extraction."],
        })
        count += 1

    # ---- Metrics (from evidence_intel.compute_metrics, definitions verbatim)
    metric_defs = [
        ("AFK-MET-0001", "avg_order_value", "Average order value", "INR",
         "sum(invoice.amount) / count(invoices with amount)", "contextual",
         ["invoices.amount"]),
        ("AFK-MET-0002", "avg_discount_pct", "Average discount percentage", "percent",
         "100 * sum(discount) / sum(amount + discount) over invoices with both fields", "lower_is_better",
         ["invoices.amount", "invoices.discount"]),
        ("AFK-MET-0003", "avg_monthly_revenue", "Average monthly invoiced revenue", "INR",
         "sum(amount) grouped by month(date), averaged over months present", "higher_is_better",
         ["invoices.amount", "invoices.date"]),
        ("AFK-MET-0004", "repeat_customer_rate", "Repeat customer rate", "percent",
         "100 * customers appearing on >1 invoice / distinct customers (requires >=3 distinct)", "higher_is_better",
         ["invoices.customer"]),
        ("AFK-MET-0005", "lead_count", "Uploaded lead count", "count",
         "count(lead records)", "contextual", ["leads"]),
        ("AFK-MET-0006", "top_lead_source", "Highest-volume lead source", "categorical",
         "mode(lead.source)", "contextual", ["leads.source"]),
        ("AFK-MET-0007", "lead_conversion_pct", "Close rate on decided leads", "percent",
         "100 * won / (won + lost) over leads with decisive status; open leads excluded (requires >=3 decided)",
         "higher_is_better", ["leads.status"]),
    ]
    met_ids = {}
    for oid, key, name, unit, formula, direction, fields in metric_defs:
        met_ids[key] = oid
        write("metrics", {
            "id": oid, "type": "metric", "name": name, "version": "1.0.0",
            "status": "hypothesis", "owner": "chief_pattern_scientist",
            "description": f"Computed metric '{key}' (extracted verbatim from M3.2 evidence_intel).",
            "definition": name, "unit": unit, "computation": formula,
            "direction": direction, "evidence_fields_required": fields,
            "todos": ["TODO(research): healthy_range and danger_range require benchmark data (M4) — not invented here."],
        })
        count += 1

    # ---- Constraints + Detection Rules (from engine rules) -----------------
    con_map = {  # dimension key -> constraint id
        "demand": "AFK-CON-0001", "qualification": "AFK-CON-0002",
        "conversion": "AFK-CON-0003", "pricing": "AFK-CON-0004",
        "retention": "AFK-CON-0005", "founder_dependency": "AFK-CON-0006",
    }
    mechanisms = {
        "demand": "Insufficient or fragile lead flow caps every downstream stage; no downstream improvement can exceed top-of-funnel volume.",
        "qualification": "Selling time spent on wrong-fit leads starves right-fit leads of attention, lowering effective capacity.",
        "conversion": "Interest fails to become revenue through weak follow-up discipline or an underperforming sales conversation.",
        "pricing": "Value created is not captured: underpricing, stale prices, or habitual discounting leak margin on every transaction.",
        "retention": "Earned customers do not return, forcing growth spend to refill a leaking bucket.",
        "founder_dependency": "Revenue knowledge and closing ability concentrated in the founder caps throughput at one person's hours and blocks delegation.",
    }
    for key, cid in con_map.items():
        write("constraints", {
            "id": cid, "type": "constraint", "name": f"{ce.DIMENSIONS[key]['label']} Constraint",
            "version": "1.0.0", "status": "hypothesis", "owner": "chief_pattern_scientist",
            "description": f"Recurring limitation pattern in the {ce.DIMENSIONS[key]['label']} system (extracted from M2 engine).",
            "definition": mechanisms[key], "mechanism": mechanisms[key],
            "affected_systems": [sys_ids[key]],
            "relationships": [{"type": "part_of", "target": sys_ids[key], "confidence": "hypothesized"}],
            "todos": ["TODO(research): symptoms/root-causes/differential sections pending Constraint Library extraction.",
                      "TODO(research): leading/lagging indicators pending accepted research.",
                      "TODO(validation): zero case studies — cannot rise above hypothesis."],
        })
        count += 1

    # Detection rules: extracted from the engine's rule functions, thresholds verbatim.
    det_rules = [
        ("AFK-DET-0001", "demand", "Thin lead flow", "leads_per_month < 10", 30),
        ("AFK-DET-0002", "demand", "Single-source demand concentration", "lead_sources_count == 'One'", 25),
        ("AFK-DET-0003", "demand", "No consistent marketing", "marketing_active == 'No'", 20),
        ("AFK-DET-0004", "demand", "Sporadic marketing", "marketing_active == 'Sporadic'", 10),
        ("AFK-DET-0005", "qualification", "No qualification process", "qualification_process startswith 'No real qualification'", 30),
        ("AFK-DET-0006", "qualification", "Low lead worthiness", "pct_leads_worth_it < 30", 25),
        ("AFK-DET-0007", "conversion", "Low close rate on serious leads", "conversion_close_rate < 30", 22),
        ("AFK-DET-0008", "conversion", "Insufficient follow-up persistence", "conversion_followups in ('1', '2')", 20),
        ("AFK-DET-0009", "conversion", "Founder-owned follow-up and closing", "conversion_owner in ('Founder only', 'Founder leads most deals')", 18),
        ("AFK-DET-0010", "conversion", "Undocumented sales process", "conversion_process == \"Mostly in people's heads\"", 15),
        ("AFK-DET-0023", "conversion", "Long sales cycle", "conversion_cycle_days > 90", 10),
        ("AFK-DET-0011", "pricing", "Self-admitted underpricing", "pricing_confidence == 'Probably underpriced'", 25),
        ("AFK-DET-0012", "pricing", "Untested pricing", "pricing_confidence == 'Honestly, no idea'", 20),
        ("AFK-DET-0013", "pricing", "Prices never changed", "last_price_change == 'Never'", 15),
        ("AFK-DET-0014", "pricing", "Habitual discounting", "discounting == 'Most deals'", 20),
        ("AFK-DET-0015", "retention", "Low repeat rate in repeat model", "repeat_rate < 30 and revenue_model in repeat-revenue models", 30),
        ("AFK-DET-0016", "retention", "Churn reasons unknown", "churn_reason_known == 'No'", 20),
        ("AFK-DET-0017", "retention", "No retention process", "retention_process == 'None'", 15),
        ("AFK-DET-0018", "founder_dependency", "Founder in every sale", "founder_in_every_sale == 'Yes, every deal'", 25),
        ("AFK-DET-0019", "founder_dependency", "Undocumented sales process", "documented_sales_process == 'No'", 15),
    ]
    for oid, dim, name, logic, penalty in det_rules:
        write("detection_rules", {
            "id": oid, "type": "detection_rule", "name": name, "version": "1.0.0",
            "status": "hypothesis", "owner": "chief_pattern_scientist",
            "description": f"Deterministic detection rule for {con_map[dim]} (threshold extracted verbatim from M2 engine).",
            "constraint_id": con_map[dim],
            "logic": logic,
            "penalty": penalty,
            "threshold_basis": "operator_judgment",
            "evidence_map": {"required": [{"kind": "questionnaire", "fields": [logic.split()[0]]}],
                             "missing_behavior": "rule does not fire; field appears in missing-evidence guidance"},
            "relationships": [{"type": "detects", "target": con_map[dim], "confidence": "hypothesized"}],
            "todos": ["TODO(validation): threshold has operator_judgment basis only; requires calibration against case studies."],
        })
        count += 1

    # M3.2 contradiction rules as detection rules over evidence metrics
    contra_rules = [
        ("AFK-DET-0020", "pricing", "Pricing belief vs measured discounting",
         "pricing_confidence in ('About right','Premium and defensible') and avg_discount_pct >= 15",
         ["AFK-MET-0002"]),
        ("AFK-DET-0021", "pricing", "'Rarely discount' vs discount data",
         "discounting == 'Rarely' and avg_discount_pct >= 15", ["AFK-MET-0002"]),
        ("AFK-DET-0022", "retention", "Stated vs measured repeat rate",
         "abs(repeat_rate - repeat_customer_rate) >= 20", ["AFK-MET-0004"]),
    ]
    for oid, dim, name, logic, mets in contra_rules:
        write("detection_rules", {
            "id": oid, "type": "detection_rule", "name": name, "version": "1.0.0",
            "status": "hypothesis", "owner": "chief_pattern_scientist",
            "description": "Contradiction rule: founder belief vs business evidence (extracted verbatim from M3.2).",
            "constraint_id": con_map[dim], "logic": logic,
            "threshold_basis": "operator_judgment",
            "evidence_map": {"required": [{"kind": "invoices", "min_rows": 1}],
                             "missing_behavior": "no contradiction is emitted without evidence"},
            "relationships": ([{"type": "detects", "target": con_map[dim], "confidence": "hypothesized"}] +
                              [{"type": "requires", "target": m, "confidence": "validated"} for m in mets]),
            "todos": ["TODO(validation): thresholds (15%, 20pts) require calibration against real businesses."],
        })
        count += 1

    # ---- Treatments (from engine._CONSTRAINT_PLAYBOOK, verbatim) -----------
    for i, (key, play) in enumerate(ce._CONSTRAINT_PLAYBOOK.items(), start=1):
        write("treatments", {
            "id": f"AFK-TRT-{i:04d}", "type": "treatment",
            "name": f"First-line treatment: {ce.DIMENSIONS[key]['label']}",
            "version": "1.0.0", "status": "hypothesis", "owner": "chief_pattern_scientist",
            "description": f"Recommended next step for the {ce.DIMENSIONS[key]['label']} constraint (extracted verbatim from M2 playbook).",
            "definition": play["next_step"], "mechanism": mechanisms[key],
            "treats": [con_map[key]],
            "expected_outcome": {"uplift_heuristic_fraction_of_annual_revenue": play["uplift"],
                                 "basis": "operator_judgment heuristic; displayed to users as a directional estimate with formula"},
            "relationships": [{"type": "treats", "target": con_map[key], "confidence": "hypothesized"}],
            "todos": ["TODO(research): contraindications not yet specified by accepted research — do not assume none exist.",
                      "TODO(research): expected_timeframe, failure_criteria, monitoring pending Treatment Methodology.",
                      "TODO(validation): uplift fraction is a heuristic; zero outcome observations exist."],
        })
        count += 1

    # ---- Confidence model (M3.2, verbatim) ---------------------------------
    write("confidence_models", {
        "id": "AFK-CFM-0001", "type": "confidence_model", "name": "Evidence-weighted confidence v1",
        "version": "1.0.0", "status": "hypothesis", "owner": "chief_epistemologist",
        "description": "The active confidence model (extracted verbatim from M3.2 evidence_intel).",
        "formula": ("per-dimension: questionnaire_coverage * 0.4 + (evidence_kinds_present/kinds_useful) "
                    "* 0.6 * avg_data_quality; dimensions with no useful evidence kind: questionnaire_coverage * 0.7; "
                    "overall = mean(per-dimension)"),
        "rationale": "Self-reported answers are hypotheses and cap at 40%; measured evidence supplies the remainder, scaled by data quality.",
        "questionnaire_ceiling": evi.QUESTIONNAIRE_CEILING,
        "todos": ["TODO(research): the 40% ceiling and 0.7 no-evidence factor are operator judgment pending epistemology research."],
    })
    count += 1

    # ---- Questionnaire items (M2 audit, verbatim) ---------------------------
    for i, q in enumerate(ce.QUESTIONS, start=1):
        write("questionnaire", {
            "id": f"AFK-QUE-{i:04d}", "type": "questionnaire_item", "name": q["label"],
            "version": "1.0.0", "status": "hypothesis", "owner": "chief_pattern_scientist",
            "description": f"Revenue Audit question '{q['id']}' (extracted verbatim from M2).",
            "text": q["label"], "answer_type": q["type"],
            "options": q.get("options"), "engine_field": q["id"], "section": q["section"],
            "evidence_class": "self_report",
        })
        count += 1

    # ---- Evidence rules (M3.2 data-quality, summarized faithfully) ----------
    for i, (kind, crit) in enumerate({
        "invoices": ["amount present on >=95% rows", "parseable date on >=95% rows",
                     "customer-name near-duplicates penalized"],
        "leads": ["status present on >=80% rows", "source present on >=80% rows"],
    }.items(), start=1):
        write("evidence_rules", {
            "id": f"AFK-EVR-{i:04d}", "type": "evidence_rule", "name": f"Quality criteria: {kind}",
            "version": "1.0.0", "status": "hypothesis", "owner": "chief_epistemologist",
            "description": f"Data-quality criteria for {kind} evidence (extracted from M3.2 data_quality).",
            "evidence_kind": kind, "quality_criteria": crit,
            "todos": ["TODO(research): freshness windows and minimum row counts pending Evidence Philosophy extraction."],
        })
        count += 1

    print(f"Extracted {count} knowledge objects into {K}")


if __name__ == "__main__":
    main()

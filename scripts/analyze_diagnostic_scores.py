"""Score sensitivity analysis for current diagnostic engine."""
from backend.app.core import engine as ce
from backend.tests.test_engine import FULL_ANSWERS


def analyze(label, answers):
    h = ce.compute_health(answers)
    print(f"\n=== {label} ===")
    if not h.get("sufficient"):
        print("INSUFFICIENT:", h.get("message"))
        return
    print(f"Health: {h['health_score']} ({h['risk_level']})")
    print(f"Primary: {h['primary_constraint']['label']} @ {h['primary_constraint']['score']}")
    for d in h["dimensions"]:
        if d["score"] is None:
            continue
        pens = sum(f["penalty"] for f in d["findings"])
        status = "HEALTHY" if d["score"] >= 75 else ("PRESSURE" if d["score"] >= 55 else "CONSTRAINT")
        print(f"  {d['key']:20} {d['score']:3} ({status}) penalties={pens} n={len(d['findings'])}")


if __name__ == "__main__":
    analyze("FULL_ANSWERS (clearly troubled founder)", FULL_ANSWERS)

    # Founder says "need more leads" but has conversion/pricing problems
    bad_conv = dict(FULL_ANSWERS)
    bad_conv.update({
        "conversion_close_rate": 15,
        "conversion_followups": "1",
        "conversion_owner": "Founder only",
    })
    analyze("Worse conversion", bad_conv)

    # "Healthy-looking" answers that still hide issues
    soft = dict(FULL_ANSWERS)
    soft.update({
        "leads_per_month": 50,
        "lead_sources_count": "Two or three",
        "marketing_active": "Yes, systematic",
        "qualification_process": "Documented criteria the team follows",
        "pct_leads_worth_it": 55,
        "conversion_close_rate": 35,
        "conversion_followups": "3",
        "conversion_owner": "Mostly team",
        "conversion_process": "Partially documented",
        "pricing_confidence": "About right",
        "discounting": "Sometimes",
        "repeat_rate": 50,
        "founder_in_every_sale": "Most deals",
        "documented_sales_process": "Yes",
    })
    analyze("Soft answers (founder thinks they're OK)", soft)
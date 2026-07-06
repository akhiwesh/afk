"""End-to-end audit wizard walkthrough against a live server."""
import json
import sys
import httpx

BASE = "http://127.0.0.1:8000/api"
EMAIL = "wizard-e2e@test.com"
PASSWORD = "StrongPass1"

MODULE_ANSWERS = {
    "context": {
        "business_type": "B2B services / agency",
        "industry": "Consulting",
        "team_size": 6,
        "growth_stage": "Early revenue (finding repeatability)",
        "monthly_revenue": 850000,
        "revenue_model": "Mixed",
        "avg_deal_value": 150000,
    },
    "demand": {
        "leads_per_month": 14,
        "lead_sources_count": "One",
        "primary_lead_source": "Referrals / word of mouth",
        "marketing_active": "Sporadic",
    },
    "qualification": {
        "qualification_process": "Informal gut-feel",
        "pct_leads_worth_it": 40,
    },
    "conversion": {
        "conversion_close_rate": 22,
        "conversion_followups": "2",
        "conversion_owner": "Founder leads most deals",
        "conversion_process": "Mostly in people's heads",
        "conversion_cycle_days": 35,
    },
    "pricing": {
        "pricing_confidence": "Probably underpriced",
        "last_price_change": "Never",
        "discounting": "Sometimes",
    },
    "retention": {
        "repeat_rate": 45,
        "churn_reason_known": "Partially / anecdotally",
        "retention_process": "Ad-hoc",
    },
    "operations": {
        "founder_in_every_sale": "Yes, every deal",
        "documented_sales_process": "No",
    },
    "reflection": {
        "revenue_goal_12m": 2500000,
        "self_diagnosis": "Need more leads",
        "biggest_worry": "Churn",
    },
}


def main():
    with httpx.Client(timeout=30) as c:
        # Register (ignore if exists)
        c.post(f"{BASE}/auth/register", json={
            "email": EMAIL, "password": PASSWORD,
            "full_name": "Wizard Tester", "organization_name": "Wizard E2E Co",
        })
        login = c.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if login.status_code != 200:
            print("LOGIN FAILED", login.status_code, login.text)
            sys.exit(1)
        token = login.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        print("=== AUDIT WIZARD E2E ===\n")

        state = c.get(f"{BASE}/intelligence/audit/modules", headers=h).json()
        print(f"Start: {state['systems_complete']}/{state['systems_total']} systems complete")
        print(f"Current module: {state['current_module']}\n")

        for mod in state["modules"]:
            mid = mod["id"]
            answers = MODULE_ANSWERS.get(mid, {})
            print(f"--- {mod['title']} ({mid}) ---")
            print(f"  Hook: {mod['hook']}")

            res = c.put(f"{BASE}/intelligence/audit/modules/{mid}", headers=h,
                        json={"answers": answers}).json()

            payoff = res["payoff"]
            print(f"  Status: {payoff.get('status')}")
            print(f"  Headline: {payoff.get('headline', '')[:120]}...")
            if payoff.get("verdict"):
                print(f"  Verdict: {payoff['verdict']}")
            if payoff.get("dimension"):
                print(f"  Score: {payoff['dimension']['score']}/100 (conf {payoff['dimension']['confidence']})")
            print(f"  Next: {res.get('next_module')}")
            print()

        health = c.get(f"{BASE}/intelligence/health", headers=h).json()
        print("=== FULL DIAGNOSIS ===")
        print(f"  Sufficient: {health.get('sufficient')}")
        print(f"  Health score: {health.get('health_score')}")
        print(f"  Primary constraint: {(health.get('primary_constraint') or {}).get('label')}")
        print(f"  Confidence: {health.get('confidence')}")
        print(f"  Contradictions: {len(health.get('contradictions') or [])}")

        twin = c.get(f"{BASE}/intelligence/twin", headers=h).json()
        print(f"\n=== TWIN ===")
        print(f"  Narrative: {(twin.get('narrative') or '')[:100]}...")
        print(f"  Constraints flagged: {len(twin.get('constraints') or [])}")

        timeline = c.get(f"{BASE}/intelligence/memory/timeline", headers=h).json()
        types = [e["type"] for e in timeline[:8]]
        print(f"\n=== MEMORY (recent) ===")
        print(f"  Events: {types}")

        onboarding = c.get(f"{BASE}/intelligence/onboarding", headers=h).json()
        print(f"\n=== ONBOARDING ===")
        print(f"  Diagnosis ready: {onboarding.get('diagnosis_ready')}")
        for step in onboarding.get("steps", []):
            print(f"  - {step['label']}: {'done' if step['done'] else 'pending'}")

        print("\n=== E2E PASS ===")


if __name__ == "__main__":
    main()
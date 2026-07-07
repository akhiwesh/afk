"""Live-server test for Conversion System v2 audit module."""
import sys
import httpx

BASE = "http://127.0.0.1:8000/api"
EMAIL = "conversion-test@test.com"
PASSWORD = "StrongPass1"

SPEC_ANSWERS = {
    "conversion_close_rate": 32,
    "conversion_followups": "2",
    "conversion_owner": "Founder leads most deals",
    "conversion_process": "Mostly in people's heads",
    "conversion_cycle_days": 55,
}

EXPECTED_QIDS = [
    "conversion_close_rate",
    "conversion_followups",
    "conversion_owner",
    "conversion_process",
    "conversion_cycle_days",
]


def main():
    with httpx.Client(timeout=30) as c:
        c.post(f"{BASE}/auth/register", json={
            "email": EMAIL,
            "password": PASSWORD,
            "full_name": "Conversion Tester",
            "organization_name": "Conversion Test Co",
        })
        login = c.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if login.status_code != 200:
            print("LOGIN FAILED", login.status_code, login.text)
            sys.exit(1)
        token = login.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        print("=== CONVERSION AUDIT LIVE TEST ===\n")

        state = c.get(f"{BASE}/intelligence/audit/modules", headers=h).json()
        conv = next(m for m in state["modules"] if m["id"] == "conversion")
        qids = [q["id"] for q in conv["questions"]]
        assert qids == EXPECTED_QIDS, f"Unexpected questions: {qids}"
        print("PASS: 5 conversion v2 questions loaded")
        for q in conv["questions"]:
            print(f"  - {q['id']} ({q['type']}): {q['label'][:60]}...")

        res = c.put(
            f"{BASE}/intelligence/audit/modules/conversion",
            headers=h,
            json={"answers": SPEC_ANSWERS},
        ).json()
        payoff = res["payoff"]
        assert payoff["ready"], payoff
        score = payoff["dimension"]["score"]
        sf = payoff.get("system_finding") or {}

        assert score == 47, f"Expected score 47, got {score}"
        assert sf.get("status") == "Critical", sf
        assert "Score: 47/100 (Critical)" in sf.get("formatted", ""), sf.get("formatted", "")[:300]
        for key in ("finding", "root_cause", "business_impact", "recommended_action", "expected_outcome"):
            assert sf.get(key), f"Missing system_finding.{key}"

        print(f"\nPASS: Score {score}/100 ({sf['status']})")
        print(f"PASS: Headline: {payoff.get('headline', '')[:100]}...")
        print(f"PASS: Verdict: {payoff.get('verdict')}")
        print(f"PASS: Next module -> {res.get('next_module')}")
        print("\n--- Structured Finding ---")
        print(sf["formatted"])
        print("\n=== CONVERSION AUDIT TEST PASSED ===")


if __name__ == "__main__":
    main()
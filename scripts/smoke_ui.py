"""Headless smoke test for diagnostic UI (audit + diagnosis pages)."""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
EMAIL = "uitest@afk.dev"
PASSWORD = "StrongPass1"


def main():
    results = []
    with sync_playwright() as p:
        for channel in ("msedge", "chrome", None):
            try:
                browser = p.chromium.launch(headless=True, channel=channel) if channel else p.chromium.launch(headless=True)
                break
            except Exception as e:
                results.append(f"launch {channel or 'bundled'}: {e}")
                browser = None
        if not browser:
            print("BROWSER_LAUNCH_FAILED")
            print("\n".join(results))
            return 1

        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{BASE}/#login", wait_until="networkidle")

        page.fill('input[type="email"], input[name="email"], #email', EMAIL)
        page.fill('input[type="password"], input[name="password"], #password', PASSWORD)
        page.click('button[type="submit"], .btn-primary')
        page.wait_for_timeout(1500)

        page.goto(f"{BASE}/#audit", wait_until="networkidle")
        page.wait_for_timeout(2000)

        audit_checks = {
            "diag-hero": page.locator(".diag-hero").count(),
            "diag-qcard": page.locator(".diag-qcard").count(),
            "diag-choice": page.locator(".diag-choice").count(),
            "diag-evidence": page.locator(".diag-evidence").count(),
        }
        print("AUDIT", json.dumps(audit_checks))

        page.goto(f"{BASE}/#diagnosis", wait_until="networkidle")
        page.wait_for_timeout(2500)

        health_checks = {
            "diag-hero": page.locator(".diag-hero").count(),
            "diag-gauge-legend": page.locator(".diag-gauge-legend").count(),
            "diag-status-pill": page.locator(".diag-status-pill").count(),
            "diag-section-label": page.locator(".diag-section-label").count(),
        }
        print("HEALTH", json.dumps(health_checks))
        print("HEALTH_SCORE_TEXT", page.locator("text=/100").first.inner_text() if page.locator("text=/100").count() else "none")

        page.screenshot(path="scripts/smoke_audit.png", full_page=True)
        page.goto(f"{BASE}/#diagnosis", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path="scripts/smoke_diagnosis.png", full_page=True)

        browser.close()

    ok = audit_checks["diag-hero"] >= 1 and health_checks["diag-hero"] >= 1
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
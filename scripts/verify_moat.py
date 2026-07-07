"""CLI: machine-verify AFK-MOA-0001 competitive moat scorecard."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.knowledge_engine.moat_scorecard import compute_moat_scorecard  # noqa: E402


def main():
    card = compute_moat_scorecard()
    print(json.dumps(card, indent=2))
    failed = [p for p in card["pillars"] if not p["passed"]]
    if failed:
        print(f"\nMOAT FAIL: {len(failed)} pillar(s) not passing", file=sys.stderr)
        for p in failed:
            print(f"  - {p['pillar_id']}", file=sys.stderr)
        sys.exit(1)
    print(f"\nMOAT PASS: score {card['moat_score']}/100 — infrastructure ready to outperform fluent-only AI tools.")


if __name__ == "__main__":
    main()
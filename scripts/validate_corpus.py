"""Run AFK-VAL-0001 corpus scorecard — no fabricated results."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.knowledge_engine.validation_framework import score_corpus


def main():
    report = score_corpus()
    print(json.dumps(report, indent=2, default=str))
    if not report.get("calibration_ready"):
        print("\nNote: calibration_ready=false — corpus gate requires N≥10 cases.", file=sys.stderr)


if __name__ == "__main__":
    main()
import json
from datetime import datetime, timezone, timedelta

from backend.app.core.twin_longitudinal import analyze_trajectory


class _Snap:
    def __init__(self, health, constraint, dims, at):
        self.health_score = health
        self.primary_constraint = constraint
        self.dimensions_json = json.dumps(dims)
        self.created_at = at


def test_trajectory_requires_two_snapshots():
    now = datetime.now(timezone.utc)
    one = [_Snap(50, "Conversion", {"conversion": 25}, now)]
    assert analyze_trajectory(one)["sufficient"] is False

    two = [
        _Snap(55, "Pricing", {"pricing": 60, "conversion": 30}, now),
        _Snap(50, "Conversion", {"pricing": 55, "conversion": 25}, now - timedelta(days=30)),
    ]
    t = analyze_trajectory(two)
    assert t["sufficient"]
    assert t["health_delta"] == 5
    assert t["constraint_changed"] is True
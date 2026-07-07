"""Longitudinal Business Twin analysis from DiagnosisSnapshot history."""
import json
from datetime import datetime


def analyze_trajectory(snapshots: list) -> dict:
    """Deterministic delta analysis. snapshots: DiagnosisSnapshot rows, newest first."""
    if not snapshots:
        return {"sufficient": False, "reason": "No diagnosis history yet."}
    if len(snapshots) < 2:
        latest = snapshots[0]
        return {
            "sufficient": False,
            "reason": "One diagnosis on record — trajectory requires at least two runs.",
            "latest": _snap_summary(latest),
        }

    latest, previous = snapshots[0], snapshots[1]
    cur_dims = json.loads(latest.dimensions_json or "{}")
    prev_dims = json.loads(previous.dimensions_json or "{}")

    dimension_deltas = []
    for key in set(cur_dims) | set(prev_dims):
        cur = cur_dims.get(key)
        prev = prev_dims.get(key)
        if cur is None or prev is None:
            continue
        delta = cur - prev
        if delta != 0:
            dimension_deltas.append({"key": key, "from": prev, "to": cur, "delta": delta})

    dimension_deltas.sort(key=lambda x: x["delta"])

    return {
        "sufficient": True,
        "health_delta": latest.health_score - previous.health_score,
        "health_from": previous.health_score,
        "health_to": latest.health_score,
        "constraint_changed": latest.primary_constraint != previous.primary_constraint,
        "constraint_from": previous.primary_constraint,
        "constraint_to": latest.primary_constraint,
        "period_days": _days_between(previous.created_at, latest.created_at),
        "improved_dimensions": [d for d in dimension_deltas if d["delta"] > 0],
        "declined_dimensions": [d for d in dimension_deltas if d["delta"] < 0],
        "latest_at": latest.created_at.isoformat(),
        "previous_at": previous.created_at.isoformat(),
        "interpretation": _interpret(latest, previous, dimension_deltas),
    }


def _snap_summary(snap) -> dict:
    return {
        "health_score": snap.health_score,
        "primary_constraint": snap.primary_constraint,
        "at": snap.created_at.isoformat(),
    }


def _days_between(a: datetime, b: datetime) -> int:
    return max(0, (b - a).days)


def _interpret(latest, previous, deltas) -> str:
    parts = []
    hd = latest.health_score - previous.health_score
    if hd > 0:
        parts.append(f"Revenue Health improved {hd} points over the period.")
    elif hd < 0:
        parts.append(f"Revenue Health declined {abs(hd)} points — pressure increased.")
    else:
        parts.append("Revenue Health unchanged between runs.")
    if latest.primary_constraint != previous.primary_constraint:
        parts.append(
            f"Primary constraint moved from {previous.primary_constraint} to {latest.primary_constraint}."
        )
    if deltas:
        worst = min(deltas, key=lambda x: x["delta"])
        if worst["delta"] < 0:
            parts.append(f"Largest decline: {worst['key']} ({worst['delta']}).")
    return " ".join(parts)
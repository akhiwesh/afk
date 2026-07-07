"""Case-study calibration probes — compare recorded observations to engine logic.

Does NOT invent benchmarks. Uses only dimension_scores and optional stored metrics.
"""
from backend.app.core import engine as ce


def replay_priority_from_observation(
    observation: dict,
    evidence_metrics: dict | None = None,
) -> dict:
    """Deterministic replay: what would AFK-PRI-0001 pick from stored scores?"""
    scores = observation.get("dimension_scores") or {}
    if not scores:
        return {"replayable": False, "reason": "observation lacks dimension_scores"}

    adjustments = ce.compute_evidence_priority_adjustments(evidence_metrics)
    ranking = []
    for key, score in scores.items():
        if key not in ce.DIMENSIONS or score is None:
            continue
        pri = ce.compute_constraint_priority(key, int(score), adjustments)
        ranking.append({
            "key": key,
            "label": ce.DIMENSIONS[key]["label"],
            "score": int(score),
            **pri,
        })
    if not ranking:
        return {"replayable": False, "reason": "no valid dimension keys in observation"}

    ranking.sort(key=lambda x: (-x["priority_score"], x["score"]))
    lowest = min(ranking, key=lambda x: x["score"])
    engine_pick = ranking[0]
    recorded = observation.get("primary_constraint")

    aligned_impact = recorded == engine_pick["label"]
    aligned_severity = recorded == lowest["label"]

    divergence = None
    if not aligned_impact:
        divergence = (
            f"Recorded primary '{recorded}' differs from {ce.PRIORITY_MODEL_ID} pick "
            f"'{engine_pick['label']}' (score {engine_pick['score']}, priority {engine_pick['priority_score']}). "
            f"Lowest score was {lowest['label']} ({lowest['score']}). "
            "Capture may predate impact priority, lack evidence metrics in replay, or reflect expert override."
        )

    return {
        "replayable": True,
        "model_id": ce.PRIORITY_MODEL_ID,
        "recorded_primary": recorded,
        "engine_primary_key": engine_pick["key"],
        "engine_primary_label": engine_pick["label"],
        "lowest_score_key": lowest["key"],
        "lowest_score_label": lowest["label"],
        "aligned_with_impact_priority": aligned_impact,
        "aligned_with_lowest_score": aligned_severity,
        "evidence_adjustments_applied": adjustments or None,
        "divergence": divergence,
        "ranking": ranking,
    }
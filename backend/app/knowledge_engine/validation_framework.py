"""AFK-VAL-0001 — case-study calibration scorecard. Never fabricates agreement rates."""
from backend.app.knowledge_engine.case_calibration import replay_priority_from_observation
from backend.app.knowledge_engine.registry import load_registry


def score_case_replay(case: dict) -> dict:
    """Deterministic scorecard for one AFK-CAS-* object. Returns metrics, not pass/fail gate."""
    obs = case.get("observation") or {}
    metrics_raw = case.get("computed_metrics") or {}
    metrics = {k: v for k, v in metrics_raw.items() if isinstance(v, dict) and "value" in v}

    base = replay_priority_from_observation(obs)
    with_evidence = replay_priority_from_observation(obs, metrics) if metrics else None

    checks = {
        "primary_base_agreement": (
            base.get("aligned_with_impact_priority") if base.get("replayable") else None
        ),
        "primary_evidence_agreement": (
            with_evidence.get("aligned_with_impact_priority") if with_evidence and with_evidence.get("replayable") else None
        ),
        "lowest_score_agreement": base.get("aligned_with_lowest_score") if base.get("replayable") else None,
        "contradictions_preserved": len(case.get("contradictions") or []) > 0,
        "metrics_replayable": bool(metrics),
    }

    weights = {
        "primary_evidence_agreement": 0.4,
        "primary_base_agreement": 0.2,
        "lowest_score_agreement": 0.2,
        "contradictions_preserved": 0.1,
        "metrics_replayable": 0.1,
    }

    scored = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        val = checks[key]
        if val is None:
            continue
        weight_sum += weight
        if val:
            scored += weight

    agreement_index = round(scored / weight_sum, 3) if weight_sum else None

    return {
        "case_id": case.get("id"),
        "synthetic": case.get("synthetic") is True,
        "observed": case.get("synthetic") is False,
        "agreement_index": agreement_index,
        "checks": checks,
        "base_replay": base,
        "evidence_replay": with_evidence,
        "corpus_gate": {
            "minimum_cases": 10,
            "current_note": "Synthetic fixtures never count toward the N≥10 observed-case calibration gate.",
        },
        "protocol_id": "AFK-VAL-0001",
    }


def score_corpus(case_ids: list[str] | None = None) -> dict:
    """Score all or selected cases. Never reports fabricated corpus statistics."""
    r = load_registry()
    ids = dict.fromkeys(case_ids if case_ids is not None else [o["id"] for o in r.by_type("case_study")])
    results = []
    for cid in ids:
        case = r.get(cid)
        if case:
            results.append(score_case_replay(case))

    observed = [x for x in results if x["observed"]]
    synthetic = [x for x in results if x["synthetic"]]
    indices = [x["agreement_index"] for x in observed if x["agreement_index"] is not None]
    return {
        "protocol_id": "AFK-VAL-0001",
        "cases_scored": len(results),
        "observed_cases_scored": len(observed),
        "synthetic_cases_scored": len(synthetic),
        "unclassified_cases_scored": len(results) - len(observed) - len(synthetic),
        "per_case": results,
        "corpus_mean_agreement": round(sum(indices) / len(indices), 3) if indices else None,
        "calibration_ready": len(observed) >= 10,
        "note": "Only unique cases explicitly marked synthetic=false contribute to the corpus mean and N≥10 calibration gate; the mean is descriptive until calibration_ready is true.",
    }

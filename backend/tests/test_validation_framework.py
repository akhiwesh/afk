"""AFK-VAL-0001 validation framework tests — no fabricated corpus results."""
from backend.app.knowledge_engine.validation_framework import score_case_replay, score_corpus
from backend.app.knowledge_engine.registry import load_registry


def test_cas_0003_scorecard_with_evidence_agrees():
    case = load_registry().get("AFK-CAS-0003")
    result = score_case_replay(case)
    assert result["protocol_id"] == "AFK-VAL-0001"
    assert result["checks"]["primary_evidence_agreement"] is True
    assert result["agreement_index"] is not None
    assert result["agreement_index"] >= 0.5


def test_corpus_not_calibration_ready():
    corpus = score_corpus()
    assert corpus["cases_scored"] >= 2
    assert corpus["observed_cases_scored"] == 0
    assert corpus["synthetic_cases_scored"] == corpus["cases_scored"]
    assert corpus["calibration_ready"] is False
    assert corpus["corpus_mean_agreement"] is None


def test_synthetic_cases_never_satisfy_observed_calibration_gate():
    corpus = score_corpus(["AFK-CAS-0002"] * 10)
    assert corpus["cases_scored"] == 1
    assert corpus["observed_cases_scored"] == 0
    assert corpus["calibration_ready"] is False
    assert corpus["corpus_mean_agreement"] is None


def test_unclassified_case_cannot_count_as_observed():
    case = dict(load_registry().get("AFK-CAS-0002"))
    del case["synthetic"]
    result = score_case_replay(case)
    assert result["synthetic"] is False
    assert result["observed"] is False


def test_synthetic_case_scored_without_claiming_validation():
    from backend.app.knowledge_engine.registry import load_registry
    case = load_registry().get("AFK-CAS-0002")
    assert case["synthetic"] is True
    result = score_case_replay(case)
    assert result["base_replay"]["replayable"]
    assert result["base_replay"]["aligned_with_impact_priority"] is True
    assert result["checks"]["primary_base_agreement"] is True

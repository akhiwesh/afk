"""Thin wrappers over M3.2 legacy engine modules — migration shim for Phase A."""
from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi


def compute_health(
    answers: dict,
    evidence_kinds: dict[str, int] | None = None,
    evidence_quality: dict[str, float] | None = None,
    evidence_metrics: dict | None = None,
) -> dict:
    return ce.compute_health(answers, evidence_kinds, evidence_quality, evidence_metrics)


def compute_twin(answers: dict) -> dict:
    return ce.compute_twin(answers)


def compute_narrative(answers: dict, org_name: str | None = None) -> str | None:
    return ce.compute_narrative(answers, org_name)


def compute_dna(answers: dict) -> list[dict]:
    return ce.compute_dna(answers)


def evidence_stats(answers: dict) -> dict:
    return ce.evidence_stats(answers)


def compute_open_questions(answers: dict) -> list[str]:
    return ce.compute_open_questions(answers)


def compute_recommendation(answers: dict) -> dict | None:
    return ce.compute_recommendation(answers)


def compute_metrics(records_by_kind: dict[str, list[dict]]) -> dict:
    return evi.compute_metrics(records_by_kind)


def detect_contradictions(answers: dict, metrics: dict) -> list[dict]:
    return evi.detect_contradictions(answers, metrics)


def evidence_confidence(
    answers: dict,
    kind_counts: dict[str, int],
    quality_by_kind: dict[str, float],
) -> dict:
    return evi.evidence_confidence(answers, kind_counts, quality_by_kind)


def missing_evidence(kind_counts: dict[str, int]) -> list[dict]:
    return evi.missing_evidence(kind_counts)


def detect_drivers(metrics: dict) -> list[dict]:
    return evi.detect_drivers(metrics)
"""Inference Engine — diagnosis, contradictions, confidence."""
from backend.app.bse.adapters import legacy
from backend.app.bse.contracts.evidence import EvidenceBundle


class InferenceEngine:
    @staticmethod
    def diagnose(audit_answers: dict) -> dict:
        return legacy.compute_health(audit_answers)

    @staticmethod
    def contradictions(audit_answers: dict, metrics: dict) -> list[dict]:
        return legacy.detect_contradictions(audit_answers, metrics)

    @staticmethod
    def confidence(audit_answers: dict, evidence: EvidenceBundle) -> dict:
        return legacy.evidence_confidence(
            audit_answers,
            evidence.kind_counts,
            evidence.quality_by_kind,
        )
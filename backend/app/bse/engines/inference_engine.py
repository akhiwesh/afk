"""Inference Engine — diagnosis, contradictions, confidence."""
from backend.app.bse.adapters import legacy
from backend.app.bse.contracts.evidence import EvidenceBundle


class InferenceEngine:
    @staticmethod
    def diagnose(
        audit_answers: dict,
        evidence: EvidenceBundle | None = None,
        evidence_metrics: dict | None = None,
    ) -> dict:
        kinds = evidence.kind_counts if evidence else {}
        quality = evidence.quality_by_kind if evidence else {}
        return legacy.compute_health(audit_answers, kinds, quality, evidence_metrics)

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
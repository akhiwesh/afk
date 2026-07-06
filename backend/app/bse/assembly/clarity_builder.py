"""Assembles the clarity report — identical schema to legacy GET /health."""
import copy

from backend.app.bse.adapters import legacy
from backend.app.bse.contracts.evidence import EvidenceBundle


class ClarityBuilder:
    @staticmethod
    def assemble(
        health: dict,
        metrics: dict,
        contradictions: list[dict],
        confidence: dict,
        recommendation: dict | None,
        evidence: EvidenceBundle,
        audit_answers: dict,
    ) -> dict:
        """Build the full clarity dict. DB-only fields (changes) are added by the API layer."""
        clarity = copy.deepcopy(health)
        clarity["evidence_stats"] = legacy.evidence_stats(audit_answers)
        clarity["open_questions"] = legacy.compute_open_questions(audit_answers)
        clarity["recommendation"] = recommendation
        clarity["confidence"] = confidence["overall"]
        clarity["confidence_breakdown"] = confidence
        clarity["evidence_metrics"] = metrics
        clarity["contradictions"] = contradictions
        clarity["revenue_drivers"] = legacy.detect_drivers(metrics)
        clarity["missing_evidence"] = legacy.missing_evidence(evidence.kind_counts)
        clarity["evidence_sources"] = (
            [{
                "source": "Revenue Audit",
                "kind": "questionnaire",
                "detail": f"{clarity['evidence_stats']['audit_answers']} answers",
            }]
            + list(evidence.sources)
        )
        return clarity
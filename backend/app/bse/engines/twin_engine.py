"""Business Twin Engine — materialize living model from pipeline state."""
from backend.app.bse.adapters import legacy
from backend.app.bse.contracts.evidence import PipelineInput
from backend.app.bse.contracts.twin import TwinState


class TwinEngine:
    @staticmethod
    def materialize(
        inputs: PipelineInput,
        health: dict,
        metrics: dict,
        contradictions: list[dict],
        confidence: dict,
    ) -> TwinState:
        answers = inputs.audit_answers
        legacy_twin = legacy.compute_twin(answers)
        narrative = legacy.compute_narrative(answers, inputs.org_name)
        dna = legacy.compute_dna(answers)
        open_questions = legacy.compute_open_questions(answers)

        current_state = {
            "sufficient": health.get("sufficient", False),
            "health_score": health.get("health_score"),
            "risk_level": health.get("risk_level"),
            "primary_constraint": health.get("primary_constraint"),
            "completeness": health.get("completeness"),
        }

        constraint_state = [
            {
                "key": d["key"],
                "label": d["label"],
                "score": d["score"],
                "confidence": d["confidence"],
            }
            for d in health.get("dimensions", [])
        ]

        return TwinState(
            business_identity=legacy_twin.get("profile", {}),
            current_state=current_state,
            constraint_state=constraint_state,
            evidence_coverage=dict(inputs.evidence.kind_counts),
            confidence_map={
                "overall": confidence.get("overall"),
                "per_dimension": confidence.get("per_dimension", {}),
                "sources": confidence.get("sources", {}),
                "method": confidence.get("method"),
            },
            open_questions=open_questions,
            narrative=narrative,
            dna=dna,
            completeness=legacy_twin.get("completeness", 0),
            fields_answered=legacy_twin.get("fields_answered", 0),
            fields_total=legacy_twin.get("fields_total", 0),
            self_diagnosis=legacy_twin.get("self_diagnosis"),
            biggest_worry=legacy_twin.get("biggest_worry"),
            constraints=legacy_twin.get("constraints", []),
            strengths=legacy_twin.get("strengths", []),
        )
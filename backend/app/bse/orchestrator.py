"""DiagnosticPipeline — the Business Science Engine orchestrator."""
from datetime import datetime, timezone

from backend.app.bse.assembly.clarity_builder import ClarityBuilder
from backend.app.bse.contracts.diagnosis import PipelineOutput, Provenance
from backend.app.bse.contracts.evidence import PipelineInput
from backend.app.bse.engines.evidence_engine import EvidenceEngine
from backend.app.bse.engines.inference_engine import InferenceEngine
from backend.app.bse.engines.metric_engine import MetricEngine
from backend.app.bse.engines.treatment_engine import TreatmentEngine
from backend.app.bse.engines.twin_engine import TwinEngine
from backend.app.bse.fingerprint import input_fingerprint
from backend.app.bse.version import DEFAULT_KB_RELEASE, ENGINE_VERSION


class DiagnosticPipeline:
    @staticmethod
    def run(inputs: PipelineInput) -> PipelineOutput:
        graph = EvidenceEngine.build(inputs.evidence)
        EvidenceEngine.assess_quality(inputs.evidence)

        metrics = MetricEngine.compute(graph, inputs.evidence)
        health = InferenceEngine.diagnose(inputs.audit_answers)
        contradictions = InferenceEngine.contradictions(inputs.audit_answers, metrics)
        confidence = InferenceEngine.confidence(inputs.audit_answers, inputs.evidence)
        recommendation = TreatmentEngine.recommend(inputs.audit_answers)
        twin = TwinEngine.materialize(
            inputs, health, metrics, contradictions, confidence
        )

        clarity = ClarityBuilder.assemble(
            health=health,
            metrics=metrics,
            contradictions=contradictions,
            confidence=confidence,
            recommendation=recommendation,
            evidence=inputs.evidence,
            audit_answers=inputs.audit_answers,
        )

        provenance = Provenance(
            kb_release=inputs.kb_release or DEFAULT_KB_RELEASE,
            engine_version=ENGINE_VERSION,
            input_fingerprint=input_fingerprint(
                inputs.audit_answers,
                inputs.evidence.records_by_kind,
            ),
            computed_at=datetime.now(timezone.utc),
        )

        return PipelineOutput(
            clarity=clarity,
            twin=twin.as_dict(),
            provenance=provenance,
            graph={"nodes": [], "edges": []},
        )
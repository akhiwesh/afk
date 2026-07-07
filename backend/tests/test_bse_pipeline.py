"""BSE Phase A — DiagnosticPipeline parity with legacy assembly."""
import copy

from backend.app.core import engine as ce
from backend.app.core import evidence_intel as evi
from backend.app.bse.assembly.clarity_builder import ClarityBuilder
from backend.app.bse.contracts.evidence import EvidenceBundle, PipelineInput
from backend.app.bse.orchestrator import DiagnosticPipeline
from backend.tests.test_engine import FULL_ANSWERS

INVOICES = [
    {"invoice_id": "1", "date": "2026-01-05", "customer": "Sharma Distributors", "amount": 100000.0, "discount": 30000.0},
    {"invoice_id": "2", "date": "2026-01-18", "customer": "Mehta Traders", "amount": 80000.0, "discount": 20000.0},
    {"invoice_id": "3", "date": "2026-02-02", "customer": "Sharma Distributors", "amount": 120000.0, "discount": 40000.0},
    {"invoice_id": "4", "date": "2026-02-20", "customer": "Kwality Depot", "amount": 90000.0, "discount": 25000.0},
]


def _legacy_clarity(answers: dict, bundle: EvidenceBundle) -> dict:
    """Reproduce pre-BSE GET /health assembly (excluding DB changes)."""
    metrics = evi.compute_metrics(bundle.records_by_kind)
    health = ce.compute_health(answers, bundle.kind_counts, bundle.quality_by_kind, metrics)
    health["evidence_stats"] = ce.evidence_stats(answers)
    health["open_questions"] = ce.compute_open_questions(answers)
    health["recommendation"] = ce.compute_recommendation(answers)

    metrics = evi.compute_metrics(bundle.records_by_kind)
    conf = evi.evidence_confidence(answers, bundle.kind_counts, bundle.quality_by_kind)
    health["confidence"] = conf["overall"]
    health["confidence_breakdown"] = conf
    health["evidence_metrics"] = metrics
    health["contradictions"] = evi.detect_contradictions(answers, metrics)
    health["revenue_drivers"] = evi.detect_drivers(metrics)
    health["missing_evidence"] = evi.missing_evidence(bundle.kind_counts)
    health["evidence_sources"] = (
        [{
            "source": "Revenue Audit",
            "kind": "questionnaire",
            "detail": f"{health['evidence_stats']['audit_answers']} answers",
        }]
        + list(bundle.sources)
    )
    return health


def test_pipeline_parity_audit_only():
    inputs = PipelineInput(audit_answers=FULL_ANSWERS, evidence=EvidenceBundle.empty())
    output = DiagnosticPipeline.run(inputs)
    legacy = _legacy_clarity(FULL_ANSWERS, EvidenceBundle.empty())
    assert output.clarity == legacy


def test_pipeline_parity_with_evidence():
    bundle = EvidenceBundle(
        records_by_kind={"invoices": INVOICES},
        kind_counts={"invoices": len(INVOICES)},
        quality_by_kind={"invoices": 0.95},
        sources=({"source": "test.csv", "kind": "invoices", "detail": "4 rows",
                  "quality_pct": 95, "quality_reasons": []},),
    )
    answers = {**FULL_ANSWERS, "pricing_confidence": "About right", "discounting": "Rarely"}
    inputs = PipelineInput(audit_answers=answers, evidence=bundle)
    output = DiagnosticPipeline.run(inputs)
    legacy = _legacy_clarity(answers, bundle)
    assert output.clarity == legacy
    assert output.clarity["contradictions"]


def test_clarity_builder_matches_orchestrator():
    bundle = EvidenceBundle(
        records_by_kind={"invoices": INVOICES},
        kind_counts={"invoices": len(INVOICES)},
        quality_by_kind={"invoices": 0.9},
    )
    inputs = PipelineInput(audit_answers=FULL_ANSWERS, evidence=bundle)
    via_pipeline = DiagnosticPipeline.run(inputs).clarity

    metrics = evi.compute_metrics(bundle.records_by_kind)
    health = ce.compute_health(FULL_ANSWERS, bundle.kind_counts, bundle.quality_by_kind, metrics)
    conf = evi.evidence_confidence(FULL_ANSWERS, bundle.kind_counts, bundle.quality_by_kind)
    via_builder = ClarityBuilder.assemble(
        health=copy.deepcopy(health),
        metrics=metrics,
        contradictions=evi.detect_contradictions(FULL_ANSWERS, metrics),
        confidence=conf,
        recommendation=ce.compute_recommendation(FULL_ANSWERS),
        evidence=bundle,
        audit_answers=FULL_ANSWERS,
    )
    assert via_pipeline == via_builder


def test_pipeline_provenance_present():
    output = DiagnosticPipeline.run(
        PipelineInput(audit_answers=FULL_ANSWERS, evidence=EvidenceBundle.empty())
    )
    assert output.provenance.engine_version == "bse-1.0.0"
    assert len(output.provenance.input_fingerprint) == 64
    assert output.twin["profile"]["business_type"] == FULL_ANSWERS["business_type"]
"""Metric Engine — compute business metrics from evidence."""
from backend.app.bse.adapters import legacy
from backend.app.bse.contracts.evidence import EvidenceBundle
from backend.app.bse.contracts.graph import EvidenceGraph


class MetricEngine:
    @staticmethod
    def compute(_graph: EvidenceGraph, evidence: EvidenceBundle) -> dict:
        return legacy.compute_metrics(evidence.records_by_kind)
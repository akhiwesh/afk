"""Evidence Engine — normalize, quality, graph construction."""
from backend.app.bse.contracts.evidence import EvidenceBundle
from backend.app.bse.contracts.graph import EvidenceGraph


class EvidenceEngine:
    @staticmethod
    def build(bundle: EvidenceBundle) -> EvidenceGraph:
        """Phase A: graph stub. Phase B builds Customer→Invoice→Lead edges."""
        return EvidenceGraph.empty()

    @staticmethod
    def assess_quality(bundle: EvidenceBundle) -> dict[str, float]:
        return dict(bundle.quality_by_kind)
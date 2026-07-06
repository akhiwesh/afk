"""Immutable contracts for evidence entering the diagnostic pipeline."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class EvidenceBundle:
    """Normalized evidence ready for metric and graph engines."""
    records_by_kind: dict[str, list[dict]]
    kind_counts: dict[str, int]
    quality_by_kind: dict[str, float]
    sources: tuple[dict[str, Any], ...] = ()

    @classmethod
    def empty(cls) -> "EvidenceBundle":
        return cls(records_by_kind={}, kind_counts={}, quality_by_kind={}, sources=())


@dataclass(frozen=True)
class PipelineInput:
    """Everything the BSE needs to run one diagnosis — no DB handles."""
    audit_answers: dict[str, Any]
    evidence: EvidenceBundle = field(default_factory=EvidenceBundle.empty)
    org_name: Optional[str] = None
    kb_release: str = "legacy-hardcoded"
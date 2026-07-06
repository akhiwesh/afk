"""Business Twin state contracts — minimal v1, expands in Phase B."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class TwinState:
    business_identity: dict[str, Any]
    current_state: dict[str, Any]
    constraint_state: list[dict[str, Any]]
    evidence_coverage: dict[str, int]
    confidence_map: dict[str, Any]
    open_questions: list[str]
    narrative: Optional[str]
    dna: list[dict[str, Any]]
    completeness: float
    fields_answered: int
    fields_total: int
    self_diagnosis: Optional[str] = None
    biggest_worry: Optional[str] = None
    constraints: list[dict[str, Any]] = field(default_factory=list)
    strengths: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict:
        """Backward-compatible dict matching legacy compute_twin + narrative + dna."""
        out = {
            "profile": self.business_identity,
            "self_diagnosis": self.self_diagnosis,
            "biggest_worry": self.biggest_worry,
            "constraints": self.constraints or [],
            "strengths": self.strengths or [],
            "completeness": self.completeness,
            "fields_answered": self.fields_answered,
            "fields_total": self.fields_total,
            "narrative": self.narrative,
            "dna": self.dna,
            "current_state": self.current_state,
            "constraint_state": self.constraint_state,
            "evidence_coverage": self.evidence_coverage,
            "confidence_map": self.confidence_map,
            "open_questions": self.open_questions,
        }
        return out
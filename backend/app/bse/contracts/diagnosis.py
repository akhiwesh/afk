"""Immutable contracts for diagnostic pipeline outputs."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class Provenance:
    kb_release: str
    engine_version: str
    input_fingerprint: str
    computed_at: datetime

    def as_dict(self) -> dict:
        return {
            "kb_release": self.kb_release,
            "engine_version": self.engine_version,
            "input_fingerprint": self.input_fingerprint,
            "computed_at": self.computed_at.isoformat(),
        }


@dataclass(frozen=True)
class PipelineOutput:
    """Full result of one DiagnosticPipeline.run() — adapter-ready."""
    clarity: dict[str, Any]
    twin: dict[str, Any]
    provenance: Provenance
    graph: Optional[dict[str, Any]] = None

    def as_dict(self) -> dict:
        out = {
            "clarity": self.clarity,
            "twin": self.twin,
            "provenance": self.provenance.as_dict(),
        }
        if self.graph is not None:
            out["graph"] = self.graph
        return out
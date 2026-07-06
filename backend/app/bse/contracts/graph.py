"""Evidence graph contracts — stub in Phase A, expanded in Phase B."""
from dataclasses import dataclass, field
from typing import Any, Literal

NodeType = Literal[
    "customer", "invoice", "lead", "discount", "salesperson",
    "channel", "product", "metric", "constraint", "treatment",
    "audit_answer", "dataset",
]
EdgeType = Literal[
    "issued_by", "belongs_to", "sourced_from", "discounted_by",
    "closed_by", "measures", "suggests", "contradicts", "treats",
]


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()

    @classmethod
    def empty(cls) -> "EvidenceGraph":
        return cls()
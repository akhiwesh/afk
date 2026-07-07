"""Revenue Intelligence models: the audit is the evidence base for diagnosis."""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RevenueAudit(SQLModel, table=True):
    """One living audit per organization. Answers stored as JSON keyed by
    question id. Partial answers are valid — the engine reports confidence
    based on completeness rather than requiring completion."""
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organization.id", index=True, unique=True)
    answers_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class DiagnosisSnapshot(SQLModel, table=True):
    """One row per diagnosis computation at audit-save time. Powers
    'What changed since your last diagnosis' with real deltas."""
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)
    health_score: int
    primary_constraint: str
    dimensions_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utcnow)


class EvidenceDataset(SQLModel, table=True):
    """One uploaded file. Holds the proposed/confirmed column mapping.
    Raw rows are kept only until the mapping is confirmed, then replaced
    by normalized EvidenceRecords."""
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)
    filename: str
    dataset_type: str = Field(default="unknown")
    status: str = Field(default="pending")  # pending -> confirmed
    row_count: int = Field(default=0)
    mapping_json: str = Field(default="[]")   # column detection proposals
    raw_json: str = Field(default="[]")       # raw rows while pending
    created_at: datetime = Field(default_factory=utcnow)
    confirmed_at: Optional[datetime] = None


class EvidenceRecord(SQLModel, table=True):
    """One normalized row of business evidence, in canonical fields."""
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="evidencedataset.id", index=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)
    record_date: Optional[str] = Field(default=None, index=True)  # ISO date
    amount: Optional[float] = Field(default=None)
    data_json: str = Field(default="{}")


class BenchmarkSample(SQLModel, table=True):
    """Anonymized metric snapshot for the future Benchmark Engine (M4).
    No org names, no customer data — profile shape + computed metrics only."""
    id: Optional[int] = Field(default=None, primary_key=True)
    business_type: Optional[str] = None
    industry: Optional[str] = None
    growth_stage: Optional[str] = None
    team_size: Optional[int] = None
    revenue_band: Optional[str] = None   # e.g. "5L-10L"
    metrics_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utcnow)


class TreatmentOutcome(SQLModel, table=True):
    """Founder-reported treatment application linked to diagnosis baselines."""
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)
    constraint_key: str = Field(index=True)
    treatment_id: Optional[str] = None
    status: str = Field(default="started")  # started | completed | abandoned
    baseline_health_score: int
    baseline_dimension_score: Optional[int] = None
    followup_dimension_score: Optional[int] = None
    outcome_verdict: str = Field(default="pending")  # pending | improved | unchanged | declined | insufficient_data
    notes: Optional[str] = None
    recorded_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = None


class MemoryEvent(SQLModel, table=True):
    """Business Memory: one append-only event in an organization's history.
    The longitudinal substrate for the Timeline and the future Reasoning
    Engine. Never updated, never deleted — memory is immutable."""
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)
    event_type: str = Field(index=True)   # audit_saved | evidence_added | evidence_removed | diagnosis_computed
    occurred_at: datetime = Field(default_factory=utcnow, index=True)
    summary: str                          # human-readable, evidence-derived
    payload_json: str = Field(default="{}")  # machine detail incl. kb/object refs

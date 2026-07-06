"""CaseStudy pipeline API — draft (anonymized preview) and approve
(founder-gated write into the knowledge base as AFK-CAS-NNNN)."""
import json
import re
from datetime import date

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.core.database import get_session
from backend.app.core import engine as ce, evidence_intel as evi, cases as cs
from backend.app.knowledge_engine import registry as kreg
from backend.app.models.auth import User, Organization
from backend.app.models.intelligence import EvidenceRecord
from backend.app.api.deps import get_current_user
from backend.app.api.intelligence import _get_answers, _evidence_bundle, remember

router = APIRouter(prefix="/intelligence/cases", tags=["cases"])

CASES_DIR = kreg.KNOWLEDGE_DIR / "cases"


class ApprovePayload(BaseModel):
    case: dict            # the (possibly founder-edited) draft returned by /draft
    consent: bool         # explicit founder consent to contribute anonymized data


def _assemble(db: Session, org_id: int) -> tuple[dict, list[str]]:
    answers = _get_answers(db, org_id)
    bundle = _evidence_bundle(db, org_id)
    metrics = evi.compute_metrics(bundle["records_by_kind"])
    health = ce.compute_health(answers)
    if health.get("sufficient"):
        # Record the evidence-weighted confidence — the same number the product
        # shows — never the raw audit-completeness figure.
        conf = evi.evidence_confidence(answers, bundle["kind_counts"], bundle["quality_by_kind"])
        health["confidence"] = conf["overall"]
    contradictions = evi.detect_contradictions(answers, metrics)
    case = cs.build_case(answers, health, metrics, contradictions, bundle["kind_counts"])

    # Forbidden terms: org name + every customer name + every source filename
    org = db.get(Organization, org_id)
    forbidden = [org.name if org else ""]
    for s in bundle["sources"]:
        forbidden.append(s["source"].rsplit(".", 1)[0])
    for recs in bundle["records_by_kind"].values():
        for r in recs:
            if r.get("customer"):
                forbidden.append(r["customer"])
            if r.get("email"):
                forbidden.append(r["email"])
    return case, [f for f in set(forbidden) if f]


@router.post("/draft")
def draft_case(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    case, forbidden = _assemble(db, current_user.organization_id)
    leaks = cs.leaked_identifiers(case, forbidden)
    if leaks:
        # Never expose a leaking draft — fail closed.
        raise HTTPException(status_code=500,
                            detail=f"Anonymization check failed; identifiers leaked: {leaks}. Case not produced.")
    return {"case": case,
            "editable_fields": ["business_profile.industry"],
            "consent_text": ("Approving contributes this anonymized case to AFK's scientific knowledge "
                             "base. It contains no names, exact revenue, or customer data — review it "
                             "above; what you see is exactly what is stored.")}


@router.post("/approve")
def approve_case(payload: ApprovePayload, db: Session = Depends(get_session),
                 current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only an organization admin can contribute a case study")
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Explicit consent is required")

    # Re-run the leak check on the (possibly edited) payload — trust nothing.
    _fresh, forbidden = _assemble(db, current_user.organization_id)
    leaks = cs.leaked_identifiers(payload.case, forbidden)
    if leaks:
        raise HTTPException(status_code=422,
                            detail=f"Submitted case contains identifying terms: {leaks}. Remove them and retry.")

    # Next sequential id from files on disk
    existing = [int(m.group(1)) for f in CASES_DIR.glob("AFK-CAS-*.yaml")
                if (m := re.match(r"AFK-CAS-(\d{4})", f.name))]
    next_id = f"AFK-CAS-{(max(existing) + 1 if existing else 1):04d}"

    obj = {
        "id": next_id, "type": "case_study",
        "name": f"Case {next_id[-4:]}: {payload.case.get('business_profile', {}).get('business_type', 'business')}",
        "version": "1.0.0", "status": "observed", "owner": "chief_pattern_scientist",
        "description": "Anonymized real-business observation contributed with founder consent.",
        "created": {"by": "founder-approved ingestion pipeline", "date": str(date.today()),
                    "reason": "Real-business case study contributed via the M3.5 pipeline"},
        "synthetic": False,
        "business_profile": payload.case.get("business_profile", {}),
        "observation": payload.case.get("observation", {}),
        "computed_metrics": payload.case.get("computed_metrics", {}),
        "contradictions": payload.case.get("contradictions", []),
        "evidence_summary": payload.case.get("evidence_summary", {}),
        "outcome": payload.case.get("outcome", {}),
    }
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    with open(CASES_DIR / f"{next_id}.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, width=100)

    kreg._registry = None  # force registry reload on next access
    remember(db, current_user.organization_id, "case_contributed",
             f"Anonymized case study contributed to AFK science as {next_id}.", {"case_id": next_id})
    return {"contributed": True, "case_id": next_id}

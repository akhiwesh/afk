from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_session
from backend.app.models.auth import User, UserRole
from backend.app.models.admin import AuditLog
from backend.app.api.deps import get_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])

class AuditLogCreate(BaseModel):
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None

class FeatureFlagToggle(BaseModel):
    flag_name: str
    is_enabled: bool

# Simple in-memory feature flags store
FEATURE_FLAGS = {
    "beta_ai_workspace": True,
    "unlimited_content_generation": False,
    "live_slack_webhooks": True
}

@router.get("/users")
def get_users_list(
    db: Session = Depends(get_session),
    admin: User = Depends(get_admin_user)
):
    users = db.exec(select(User).where(User.organization_id == admin.organization_id)).all()
    # Serialize safely
    return [{
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at
    } for u in users]

@router.get("/logs", response_model=List[AuditLog])
def get_audit_logs(
    db: Session = Depends(get_session),
    admin: User = Depends(get_admin_user)
):
    return db.exec(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)).all()

@router.post("/logs", response_model=AuditLog)
def create_audit_log(
    data: AuditLogCreate,
    db: Session = Depends(get_session),
    admin: User = Depends(get_admin_user)
):
    log = AuditLog(
        action=data.action,
        user_email=admin.email,
        details=data.details,
        ip_address=data.ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.get("/flags")
def get_feature_flags(admin: User = Depends(get_admin_user)):
    return FEATURE_FLAGS

@router.post("/flags")
def toggle_feature_flag(
    data: FeatureFlagToggle,
    admin: User = Depends(get_admin_user)
):
    if data.flag_name not in FEATURE_FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    FEATURE_FLAGS[data.flag_name] = data.is_enabled
    return {"message": f"Feature flag '{data.flag_name}' updated to {data.is_enabled}", "flags": FEATURE_FLAGS}

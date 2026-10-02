from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from backend.app.core.time import utcnow

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str = Field(index=True)
    user_email: str = Field(index=True)
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

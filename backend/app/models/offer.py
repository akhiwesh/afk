"""Sales offer inquiries — concierge diagnostic applications."""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OfferInquiry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True)
    company: str
    revenue_band: str = Field(default="")
    primary_worry: str = Field(default="")
    message: str = Field(default="")
    source: str = Field(default="offer_page")
    created_at: datetime = Field(default_factory=utcnow)
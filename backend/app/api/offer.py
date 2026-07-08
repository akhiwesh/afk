"""Public offer page — diagnostic application intake."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import Session

from backend.app.core.database import get_session
from backend.app.models.offer import OfferInquiry

router = APIRouter(prefix="/offer", tags=["offer"])

REVENUE_BANDS = (
    "Under ₹5L/mo",
    "₹5L–10L/mo",
    "₹10L–25L/mo",
    "₹25L–1Cr/mo",
    "₹1Cr+/mo",
    "Prefer not to say",
)


class OfferInquiryRequest(BaseModel):
    full_name: str
    email: EmailStr
    company: str
    revenue_band: str = ""
    primary_worry: str = ""
    message: str = ""

    @field_validator("full_name", "company")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("revenue_band")
    @classmethod
    def valid_band(cls, v: str) -> str:
        v = v.strip()
        if v and v not in REVENUE_BANDS:
            raise ValueError("Invalid revenue band")
        return v


class OfferInquiryResponse(BaseModel):
    id: int
    message: str


@router.post("/inquiry", response_model=OfferInquiryResponse)
def submit_inquiry(data: OfferInquiryRequest, db: Session = Depends(get_session)):
    row = OfferInquiry(
        full_name=data.full_name,
        email=data.email,
        company=data.company,
        revenue_band=data.revenue_band,
        primary_worry=data.primary_worry.strip(),
        message=data.message.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return OfferInquiryResponse(
        id=row.id,
        message="Application received. We will reply within one business day.",
    )
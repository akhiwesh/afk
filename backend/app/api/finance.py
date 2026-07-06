from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List
from datetime import datetime

from backend.app.core.database import get_session
from backend.app.models.finance import Invoice, InvoiceStatus
from backend.app.models.crm import Client
from backend.app.models.auth import User
from backend.app.api.deps import get_team_user, get_current_user

router = APIRouter(prefix="/finance", tags=["finance"])

class InvoiceCreate(BaseModel):
    client_id: int
    amount: float
    due_date: datetime

@router.get("/invoices", response_model=List[Invoice])
def get_invoices(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    # Query invoices where client organization matches
    return db.exec(
        select(Invoice)
        .join(Client)
        .where(Client.organization_id == current_user.organization_id)
        .order_by(Invoice.created_at.desc())
    ).all()

@router.post("/invoices", response_model=Invoice)
def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    # Check if client exists in the same org
    client = db.exec(select(Client).where(
        Client.id == data.client_id,
        Client.organization_id == current_user.organization_id
    )).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found in your organization")
        
    # Generate unique invoice number
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    inv_num = f"INV-{timestamp}"
    
    invoice = Invoice(
        invoice_number=inv_num,
        amount=data.amount,
        status=InvoiceStatus.SENT,
        due_date=data.due_date,
        client_id=data.client_id
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.post("/invoices/{invoice_id}/pay")
def pay_invoice(
    invoice_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    invoice = db.exec(select(Invoice).where(Invoice.id == invoice_id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.client.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    invoice.status = InvoiceStatus.PAID
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return {"message": "Invoice paid successfully", "invoice": invoice}

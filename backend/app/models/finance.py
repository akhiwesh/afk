from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from backend.app.core.time import utcnow

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(unique=True, index=True)
    amount: float
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)
    due_date: datetime
    created_at: datetime = Field(default_factory=utcnow)
    
    client_id: int = Field(foreign_key="client.id")
    
    # Relationships
    client: "Client" = Relationship(back_populates="invoices")

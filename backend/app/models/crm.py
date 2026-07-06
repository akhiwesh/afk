from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class ClientStatus(str, Enum):
    LEAD = "lead"
    ACTIVE = "active"
    LOST = "lost"

class PipelineStage(str, Enum):
    CONTACT = "contact"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    company: str
    phone: Optional[str] = None
    status: ClientStatus = Field(default=ClientStatus.LEAD)
    pipeline_stage: PipelineStage = Field(default=PipelineStage.CONTACT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    organization_id: int = Field(foreign_key="organization.id")
    
    # Relationships
    organization: "Organization" = Relationship(back_populates="clients")
    notes: List["ClientNote"] = Relationship(back_populates="client")
    files: List["ClientFile"] = Relationship(back_populates="client")
    invoices: List["Invoice"] = Relationship(back_populates="client")

class ClientNote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    client_id: int = Field(foreign_key="client.id")
    
    # Relationships
    client: Client = Relationship(back_populates="notes")

class ClientFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    filepath: str
    file_size: int  # in bytes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    client_id: int = Field(foreign_key="client.id")
    
    # Relationships
    client: Client = Relationship(back_populates="files")

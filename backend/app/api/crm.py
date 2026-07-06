from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_session
from backend.app.models.crm import Client, ClientNote, ClientStatus, PipelineStage
from backend.app.models.auth import User
from backend.app.api.deps import get_current_user, get_team_user

router = APIRouter(prefix="/crm", tags=["crm"])

class ClientCreate(BaseModel):
    name: str
    email: str
    company: str
    phone: Optional[str] = None
    status: Optional[ClientStatus] = ClientStatus.LEAD
    pipeline_stage: Optional[PipelineStage] = PipelineStage.CONTACT

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[ClientStatus] = None
    pipeline_stage: Optional[PipelineStage] = None

class NoteCreate(BaseModel):
    content: str

@router.get("/clients", response_model=List[Client])
def get_clients(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    # Scope to current organization
    return db.exec(select(Client).where(Client.organization_id == current_user.organization_id)).all()

@router.post("/clients", response_model=Client)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    client = Client(
        name=data.name,
        email=data.email,
        company=data.company,
        phone=data.phone,
        status=data.status or ClientStatus.LEAD,
        pipeline_stage=data.pipeline_stage or PipelineStage.CONTACT,
        organization_id=current_user.organization_id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/clients/{client_id}")
def get_client_details(
    client_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    client = db.exec(select(Client).where(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    )).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    notes = db.exec(select(ClientNote).where(ClientNote.client_id == client_id).order_by(ClientNote.created_at.desc())).all()
    
    return {
        "client": client,
        "notes": notes,
        "files": client.files
    }

@router.put("/clients/{client_id}", response_model=Client)
def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    client = db.exec(select(Client).where(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    )).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # Update properties
    for key, value in data.dict(exclude_unset=True).items():
        setattr(client, key, value)
        
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.post("/clients/{client_id}/notes", response_model=ClientNote)
def add_client_note(
    client_id: int,
    data: NoteCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    client = db.exec(select(Client).where(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    )).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    note = ClientNote(content=data.content, client_id=client_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

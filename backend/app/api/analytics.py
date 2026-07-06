from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List, Dict, Any

from backend.app.core.database import get_session
from backend.app.models.crm import Client, ClientStatus
from backend.app.models.projects import Project
from backend.app.models.finance import Invoice, InvoiceStatus
from backend.app.models.auth import User
from backend.app.api.deps import get_team_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
def get_dashboard_analytics(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    # Retrieve real statistics
    org_id = current_user.organization_id
    
    total_leads = len(db.exec(select(Client).where(
        Client.organization_id == org_id, 
        Client.status == ClientStatus.LEAD
    )).all())
    
    total_clients = len(db.exec(select(Client).where(
        Client.organization_id == org_id, 
        Client.status == ClientStatus.ACTIVE
    )).all())
    
    active_projects = len(db.exec(select(Project).where(Project.organization_id == org_id)).all())
    
    invoices = db.exec(select(Invoice).join(Client).where(Client.organization_id == org_id)).all()
    total_revenue = sum(inv.amount for inv in invoices if inv.status == InvoiceStatus.PAID)
    pending_revenue = sum(inv.amount for inv in invoices if inv.status == InvoiceStatus.SENT)
    
    # Calculate conversion rate
    all_clients_count = len(db.exec(select(Client).where(Client.organization_id == org_id)).all())
    conversion_rate = 0.0
    if all_clients_count > 0:
        conversion_rate = round((total_clients / all_clients_count) * 100, 1)

    # No fabricated time series. Only computed values leave this endpoint.
    return {
        "kpis": {
            "total_leads": total_leads,
            "total_clients": total_clients,
            "active_projects": active_projects,
            "total_revenue": total_revenue,
            "pending_revenue": pending_revenue,
            "conversion_rate": conversion_rate
        }
    }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
import json

from backend.app.core.database import get_session
from backend.app.models.automation import Workflow, WorkflowExecutionLog
from backend.app.models.auth import User
from backend.app.api.deps import get_current_user, get_team_user

router = APIRouter(prefix="/automation", tags=["automation"])

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[dict]  # Will serialize to steps_json

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[dict]] = None
    is_active: Optional[bool] = None

class WorkflowExecuteRequest(BaseModel):
    trigger_data: dict

@router.get("/workflows")
def get_workflows(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    workflows = db.exec(select(Workflow).where(Workflow.organization_id == current_user.organization_id)).all()
    # Deserialize steps
    results = []
    for w in workflows:
        results.append({
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "is_active": w.is_active,
            "steps": json.loads(w.steps_json),
            "created_at": w.created_at
        })
    return results

@router.post("/workflows")
def create_workflow(
    data: WorkflowCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    w = Workflow(
        name=data.name,
        description=data.description,
        steps_json=json.dumps(data.steps),
        is_active=True,
        organization_id=current_user.organization_id
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return {
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "is_active": w.is_active,
        "steps": json.loads(w.steps_json),
        "created_at": w.created_at
    }

@router.put("/workflows/{workflow_id}")
def update_workflow(
    workflow_id: int,
    data: WorkflowUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    w = db.exec(select(Workflow).where(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    )).first()
    
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if data.name is not None:
        w.name = data.name
    if data.description is not None:
        w.description = data.description
    if data.steps is not None:
        w.steps_json = json.dumps(data.steps)
    if data.is_active is not None:
        w.is_active = data.is_active
        
    db.add(w)
    db.commit()
    db.refresh(w)
    return {
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "is_active": w.is_active,
        "steps": json.loads(w.steps_json),
        "created_at": w.created_at
    }

@router.post("/workflows/{workflow_id}/execute")
def execute_workflow(
    workflow_id: int,
    req: WorkflowExecuteRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    w = db.exec(select(Workflow).where(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    )).first()
    
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    steps = json.loads(w.steps_json)
    trigger_data = req.trigger_data
    execution_steps = []
    
    status_overall = "success"
    error_message = None
    
    # Simple simulator of workflow steps
    for step in steps:
        step_id = step.get("id")
        step_type = step.get("type")
        step_name = step.get("name", step_type)
        step_config = step.get("config", {})
        
        step_log = {
            "id": step_id,
            "name": step_name,
            "type": step_type,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "output": {}
        }
        
        try:
            if step_type == "trigger":
                step_log["output"] = {"message": "Workflow triggered successfully", "data": trigger_data}
            elif step_type == "action_ai":
                # Simulated qualification
                company_name = trigger_data.get("company", "Generic Corp")
                employees = int(trigger_data.get("employees", 10))
                qualified = employees >= 50
                step_log["output"] = {
                    "verdict": "QUALIFIED" if qualified else "NOT_QUALIFIED",
                    "reasoning": f"Analyzed {company_name} with employees={employees}. Required criteria: employees >= 50."
                }
            elif step_type == "action_email":
                recipient = trigger_data.get("email", "lead@company.com")
                step_log["output"] = {
                    "sent_to": recipient,
                    "subject": "Welcome to AFK Launch Onboarding",
                    "body": "Hi, we are processing your lead details. Glad to connect."
                }
            elif step_type == "action_crm":
                step_log["output"] = {
                    "action": "Upsert CRM Lead Record",
                    "status": "Success",
                    "record_id": 999
                }
            elif step_type == "action_slack":
                step_log["output"] = {
                    "alert_sent": True,
                    "channel": "#growth-alerts",
                    "payload": f"New Lead qualified: {trigger_data.get('name', 'Anonymous')}"
                }
            else:
                step_log["output"] = {"message": f"Executed custom step {step_name}"}
                
        except Exception as e:
            status_overall = "failed"
            error_message = str(e)
            step_log["status"] = "failed"
            step_log["error"] = error_message
            execution_steps.append(step_log)
            break
            
        execution_steps.append(step_log)

    log_record = WorkflowExecutionLog(
        status=status_overall,
        trigger_data=json.dumps(trigger_data),
        execution_steps=json.dumps(execution_steps),
        error_message=error_message,
        workflow_id=workflow_id
    )
    db.add(log_record)
    db.commit()
    db.refresh(log_record)
    
    return {
        "execution_id": log_record.id,
        "status": status_overall,
        "error_message": error_message,
        "steps": execution_steps
    }

@router.get("/workflows/{workflow_id}/logs")
def get_workflow_logs(
    workflow_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    w = db.exec(select(Workflow).where(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    )).first()
    
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    logs = db.exec(select(WorkflowExecutionLog).where(WorkflowExecutionLog.workflow_id == workflow_id).order_by(WorkflowExecutionLog.created_at.desc())).all()
    
    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "status": l.status,
            "trigger_data": json.loads(l.trigger_data),
            "execution_steps": json.loads(l.execution_steps),
            "error_message": l.error_message,
            "created_at": l.created_at
        })
    return results

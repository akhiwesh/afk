from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Workflow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    steps_json: str  # Stores JSON structure of steps
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    organization_id: int = Field(foreign_key="organization.id")
    
    # Relationships
    logs: List["WorkflowExecutionLog"] = Relationship(back_populates="workflow")

class WorkflowExecutionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(index=True)  # "success", "failed", "running"
    trigger_data: str  # JSON input details
    execution_steps: str  # JSON showing details of each step executed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    workflow_id: int = Field(foreign_key="workflow.id")
    
    # Relationships
    workflow: Workflow = Relationship(back_populates="logs")

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from backend.app.core.time import utcnow

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING)
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    
    organization_id: int = Field(foreign_key="organization.id")
    
    # Relationships
    organization: "Organization" = Relationship(back_populates="projects")
    tasks: List["Task"] = Relationship(back_populates="project")
    milestones: List["Milestone"] = Relationship(back_populates="project")

class Milestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    due_date: datetime
    is_completed: bool = Field(default=False)
    
    project_id: int = Field(foreign_key="project.id")
    
    # Relationships
    project: Project = Relationship(back_populates="milestones")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    column_index: int = Field(default=0) # For kanban positioning
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    
    project_id: int = Field(foreign_key="project.id")
    assignee_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    project: Project = Relationship(back_populates="tasks")
    assignee: Optional["User"] = Relationship(back_populates="assigned_tasks")
    comments: List["TaskComment"] = Relationship(back_populates="task")

class TaskComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=utcnow)
    
    task_id: int = Field(foreign_key="task.id")
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    task: Task = Relationship(back_populates="comments")
    user: "User" = Relationship(back_populates="comments")

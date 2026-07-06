from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_session
from backend.app.models.projects import Project, ProjectStatus, Task, TaskStatus, TaskPriority, TaskComment, Milestone
from backend.app.models.auth import User
from backend.app.api.deps import get_current_user, get_team_user

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[ProjectStatus] = ProjectStatus.PLANNING
    due_date: Optional[datetime] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.TODO
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    column_index: Optional[int] = 0
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    column_index: Optional[int] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

class CommentCreate(BaseModel):
    content: str

@router.get("", response_model=List[Project])
def get_projects(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    return db.exec(select(Project).where(Project.organization_id == current_user.organization_id)).all()

@router.post("", response_model=Project)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    project = Project(
        name=data.name,
        description=data.description,
        status=data.status or ProjectStatus.PLANNING,
        due_date=data.due_date,
        organization_id=current_user.organization_id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}/tasks")
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    project = db.exec(select(Project).where(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id
    )).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    tasks = db.exec(select(Task).where(Task.project_id == project_id)).all()
    # Add simple serialization with assignee details
    serialized_tasks = []
    for task in tasks:
        assignee = task.assignee
        serialized_tasks.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "column_index": task.column_index,
            "due_date": task.due_date,
            "assignee": {
                "id": assignee.id,
                "full_name": assignee.full_name,
                "email": assignee.email
            } if assignee else None
        })
    return serialized_tasks

@router.post("/{project_id}/tasks", response_model=Task)
def create_project_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    project = db.exec(select(Project).where(
        Project.id == project_id,
        Project.organization_id == current_user.organization_id
    )).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    task = Task(
        title=data.title,
        description=data.description,
        status=data.status or TaskStatus.TODO,
        priority=data.priority or TaskPriority.MEDIUM,
        column_index=data.column_index or 0,
        due_date=data.due_date,
        project_id=project_id,
        assignee_id=data.assignee_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    # Verify task exists and is in organization
    task = db.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    for key, value in data.dict(exclude_unset=True).items():
        setattr(task, key, value)
        
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.post("/tasks/{task_id}/comments", response_model=TaskComment)
def add_task_comment(
    task_id: int,
    data: CommentCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    task = db.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    comment = TaskComment(
        content=data.content,
        task_id=task_id,
        user_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

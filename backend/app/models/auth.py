from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"
    TEAM = "team"

class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="organization")
    clients: List["Client"] = Relationship(back_populates="organization")
    projects: List["Project"] = Relationship(back_populates="organization")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    hashed_password: str
    role: UserRole = Field(default=UserRole.TEAM)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    
    # Relationships
    organization: Optional[Organization] = Relationship(back_populates="users")
    assigned_tasks: List["Task"] = Relationship(back_populates="assignee")
    comments: List["TaskComment"] = Relationship(back_populates="user")
    generated_content: List["GeneratedContent"] = Relationship(back_populates="creator")

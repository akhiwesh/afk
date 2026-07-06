import os
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

# SQLite local database setup
DB_FILE = "database.db"
# Set database URL dynamically based on environment, default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE}")

# SQLite specific argument connect_args={"check_same_thread": False} is required
# when running multiple threads in FastAPI.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def init_db() -> None:
    # This imports all models so SQLModel metadata knows about them
    from backend.app.models.auth import User, Organization
    from backend.app.models.crm import Client, ClientNote, ClientFile
    from backend.app.models.projects import Project, Task, TaskComment, Milestone
    from backend.app.models.ai import AIConversation, AIMessage, GeneratedContent
    from backend.app.models.automation import Workflow, WorkflowExecutionLog
    from backend.app.models.finance import Invoice
    from backend.app.models.admin import AuditLog
    from backend.app.models.intelligence import RevenueAudit, DiagnosisSnapshot, EvidenceDataset, EvidenceRecord, BenchmarkSample, MemoryEvent
    
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

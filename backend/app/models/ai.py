from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from backend.app.core.time import utcnow

class AIAssistantType(str, Enum):
    MARKETING_STRATEGIST = "marketing_strategist"
    SALES_ADVISOR = "sales_advisor"
    BUSINESS_CONSULTANT = "business_consultant"
    CONTENT_CREATOR = "content_creator"
    SEO_EXPERT = "seo_expert"
    COPYWRITER = "copywriter"
    RESEARCH_ANALYST = "research_analyst"
    AUTOMATION_ENGINEER = "automation_engineer"
    PROMPT_ENGINEER = "prompt_engineer"
    GROWTH_ADVISOR = "growth_advisor"

class ContentChannel(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    THREADS = "threads"
    BLOG = "blog"
    EMAIL = "email"
    AD_COPY = "ad_copy"
    LANDING_PAGE = "landing_page"
    VIDEO_SCRIPT = "video_script"
    HOOKS = "hooks"

class AIConversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    assistant_type: AIAssistantType
    created_at: datetime = Field(default_factory=utcnow)
    
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    messages: List["AIMessage"] = Relationship(back_populates="conversation")

class AIMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str = Field(index=True)  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=utcnow)
    
    conversation_id: int = Field(foreign_key="aiconversation.id")
    
    # Relationships
    conversation: AIConversation = Relationship(back_populates="messages")

class GeneratedContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    channel: ContentChannel
    created_at: datetime = Field(default_factory=utcnow)
    
    creator_id: int = Field(foreign_key="user.id")
    
    # Relationships
    creator: "User" = Relationship(back_populates="generated_content")

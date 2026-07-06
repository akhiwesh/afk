from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os

from backend.app.core.database import get_session
from backend.app.models.ai import AIConversation, AIMessage, AIAssistantType, GeneratedContent, ContentChannel
from backend.app.models.auth import User
from backend.app.api.deps import get_current_user, get_team_user

router = APIRouter(prefix="/ai", tags=["ai"])

class ConversationCreate(BaseModel):
    title: str
    assistant_type: AIAssistantType

class MessageCreate(BaseModel):
    content: str

class ContentGenerateRequest(BaseModel):
    title: str
    channel: ContentChannel
    prompt: str
    tone: Optional[str] = "professional"

# Mock answers dictionary for high-fidelity responses
MOCK_RESPONSES = {
    AIAssistantType.MARKETING_STRATEGIST: (
        "Here is a bespoke marketing strategy based on your request:\n\n"
        "1. **Core Value Proposition**: Position your product as the ultimate operational efficiency multiplier for your target audience.\n"
        "2. **Distribution Channels**:\n"
        "   - **Primary**: LinkedIn organic and targeted content engineering (focus on problem-solution mechanics).\n"
        "   - **Secondary**: Niche community building (Slack, Discord) to foster feedback and long term retention.\n"
        "3. **Suggested 30-Day Campaign**: Build a 'Build in Public' log detailing your product journey, aiming to secure 100 beta test founders."
    ),
    AIAssistantType.SALES_ADVISOR: (
        "Here is a premium Sales script and approach for your outreach:\n\n"
        "**Subject**: Quick question regarding outbound overhead at [Company]\n\n"
        "Hi [First Name],\n\n"
        "I noticed you're scaling your team at [Company]. Most growth teams waste 20+ hours weekly manually qualifying leads.\n\n"
        "We built an automated qualification pipeline that filters prospects in real time and alerts Slack—shortening the sales cycle by 40%.\n\n"
        "Would you be open to a brief 10-minute preview this Thursday?\n\n"
        "Best,\n[Your Name]"
    ),
    AIAssistantType.BUSINESS_CONSULTANT: (
        "Based on your query, here is an executive business consultancy feedback:\n\n"
        "1. **Business Model**: Recommend a hybrid SaaS model with a low-friction usage tier and a high-ticket enterprise custom SLA.\n"
        "2. **Unit Economics**: Target a Customer Acquisition Cost (CAC) to Lifetime Value (LTV) ratio of at least 1:3 by driving inbound growth via SEO and tool-based lead magnets.\n"
        "3. **Milestone Targets**: Aim to secure 10 pilot agreements within the next 45 days to validate standard pricing assumptions."
    ),
    AIAssistantType.CONTENT_CREATOR: (
        "Here are 3 content hooks and outlines optimized for high viral engagement:\n\n"
        "- **Hook 1**: '99% of startups fail at lead generation. But this 1 simple automations script changed everything...'\n"
        "- **Hook 2**: 'We built a million dollar CRM system using zero lines of code. Here is the full backend architecture.'\n"
        "- **Hook 3**: 'The standard CRM is dead. Here is why the modern founding team is moving to AI-native execution engines.'"
    ),
    AIAssistantType.SEO_EXPERT: (
        "Here is your targeted SEO plan:\n\n"
        "1. **Focus Keywords**: 'AI growth agency platform', 'no-code workflow qualifier', 'automated B2B growth stack'.\n"
        "2. **Content Pillar Layout**: Draft a comprehensive 3,500-word guide titled 'The Ultimate Guide to AI-Native Lead Generation' and cross-link it to service subpages.\n"
        "3. **Technical Audit Action**: Optimize image layout tags and enable gzip compression to maintain a Core Web Vitals score above 90."
    ),
    AIAssistantType.COPYWRITER: (
        "Here is your high-conversion landing page copy outline:\n\n"
        "**Hero Headline**: Scale Your Growth At The Speed of AI.\n"
        "**Subheadline**: The all-in-one execution workspace that qualifies leads, builds marketing calendars, and runs workflows autonomously.\n"
        "**Call to Action**: Start Scaling Free (No credit card required)\n"
        "**Social Proof Tag**: Trusted by forward-thinking founders worldwide."
    ),
    AIAssistantType.RESEARCH_ANALYST: (
        "Here is your competitive research synthesis:\n\n"
        "1. **Market Landscape**: The AI-native SaaS market is rapidly expanding, with standard legacy platforms (Salesforce, HubSpot) lagging behind in automated LLM integrations.\n"
        "2. **Competitor Deficiencies**: Competitors usually require complex external Zapier integrations, causing high data latency and structural failure points.\n"
        "3. **AFK Advantage**: Complete unified execution, blending CRM, Kanban, AI assistants, and visual builders natively in one workspace."
    ),
    AIAssistantType.AUTOMATION_ENGINEER: (
        "Recommended automation sequence template:\n\n"
        "```json\n"
        "{\n"
        "  \"trigger\": \"Webhook - Lead Submitted\",\n"
        "  \"steps\": [\n"
        "    {\"action\": \"Filter\", \"criteria\": \"Company size > 50 employees\"},\n"
        "    {\"action\": \"AI Enrichment\", \"prompt\": \"Extract LinkedIn profile from company name\"},\n"
        "    {\"action\": \"CRM Update\", \"status\": \"Qualified Opportunity\"},\n"
        "    {\"action\": \"Slack Notify\", \"channel\": \"#sales-alerts\"}\n"
        "  ]\n"
        "}\n"
        "```"
    ),
    AIAssistantType.PROMPT_ENGINEER: (
        "Optimized Prompt structure for your assistant:\n\n"
        "```markdown\n"
        "You are an elite B2B copywriting agent. Your tone is direct, modern, and highly persuasive.\n"
        "CONSTRAINTS:\n"
        "- Never use emojis.\n"
        "- Never use buzzwords like 'synergy' or 'revolutionary'.\n"
        "- Focus strictly on quantifiable metrics (e.g., hours saved, conversion rates).\n"
        "```"
    ),
    AIAssistantType.GROWTH_ADVISOR: (
        "Here is your virality growth loop strategy:\n\n"
        "1. **Inbound Magnet**: Offer a free visual workflow sandbox builder tool. To export the workflow, the user inputs their email.\n"
        "2. **Retention Loop**: Send weekly performance reports directly comparing automated qualifications versus manual overhead savings.\n"
        "3. **Viral Incentive**: Give clients 1,000 free AI generation credits for every new organisation they refer to the platform."
    )
}

@router.get("/conversations", response_model=List[AIConversation])
def get_conversations(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return db.exec(select(AIConversation).where(AIConversation.user_id == current_user.id).order_by(AIConversation.created_at.desc())).all()

@router.post("/conversations", response_model=AIConversation)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conv = AIConversation(
        title=data.title,
        assistant_type=data.assistant_type,
        user_id=current_user.id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/conversations/{conversation_id}/messages", response_model=List[AIMessage])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conv = db.exec(select(AIConversation).where(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    )).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    return db.exec(select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at.asc())).all()

@router.post("/conversations/{conversation_id}/messages", response_model=AIMessage)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conv = db.exec(select(AIConversation).where(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    )).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # 1. Save user message
    user_msg = AIMessage(
        role="user",
        content=data.content,
        conversation_id=conversation_id
    )
    db.add(user_msg)
    
    # 2. Generate assistant response
    # In a real environment, we'd check if Gemini API key exists:
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    ai_response_text = ""
    
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Pull conversation history
            history = db.exec(select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at.asc())).all()
            
            # Setup prompt with agent specific context
            system_instructions = f"You are a premium AI assistant of type {conv.assistant_type.value}. Your tone is minimalist, elegant, extremely knowledgeable, venture-grade SaaS platform expert."
            prompt = f"{system_instructions}\n\nUser prompt: {data.content}"
            response = model.generate_content(prompt)
            ai_response_text = response.text
        except Exception as e:
            # Fallback on exception
            ai_response_text = f"Error calling AI API: {str(e)}. Fallback Response:\n\n" + MOCK_RESPONSES.get(conv.assistant_type, "Hello! How can I assist you with your growth today?")
    else:
        # Fallback to high fidelity mock
        ai_response_text = MOCK_RESPONSES.get(conv.assistant_type, "Hello! How can I assist you with your growth today?")
        
    assistant_msg = AIMessage(
        role="assistant",
        content=ai_response_text,
        conversation_id=conversation_id
    )
    db.add(assistant_msg)
    
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg

@router.post("/generate", response_model=GeneratedContent)
def generate_studio_content(
    data: ContentGenerateRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    # Generates copywriting copy directly
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    content_text = ""
    
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Write a professional copy-writing piece for the channel: {data.channel.value}. Target: {data.title}. Prompts details: {data.prompt}. Tone: {data.tone}."
            response = model.generate_content(prompt)
            content_text = response.text
        except Exception:
            content_text = f"Draft generated content for {data.title}:\n\n- Hook: 3 secrets high performing teams use to scale {data.channel.value}.\n- Body: Focus on product market fit, pipeline execution, and automation.\n- CTA: Find out how at AFK.agency"
    else:
        content_text = f"Draft generated content for {data.title} ({data.channel.value}):\n\n1. Focus on metrics: Qualify leads automatically.\n2. Scale pipeline outbound.\n3. Join the future of growth execution today at AFK."
        
    gc = GeneratedContent(
        title=data.title,
        content=content_text,
        channel=data.channel,
        creator_id=current_user.id
    )
    db.add(gc)
    db.commit()
    db.refresh(gc)
    return gc

@router.get("/content", response_model=List[GeneratedContent])
def get_saved_content(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_team_user)
):
    return db.exec(select(GeneratedContent).where(GeneratedContent.creator_id == current_user.id).order_by(GeneratedContent.created_at.desc())).all()

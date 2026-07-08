import json
from datetime import datetime, timedelta
from sqlmodel import Session, select
from backend.app.core.database import engine, init_db
from backend.app.core.security import get_password_hash
from backend.app.models.auth import User, Organization, UserRole
from backend.app.models.crm import Client, ClientStatus, PipelineStage, ClientNote
from backend.app.models.projects import Project, ProjectStatus, Task, TaskStatus, TaskPriority
from backend.app.models.ai import AIConversation, AIMessage, AIAssistantType, GeneratedContent, ContentChannel
from backend.app.models.automation import Workflow
from backend.app.models.finance import Invoice, InvoiceStatus

# Shared demo session identity — used by POST /api/auth/demo (one-click demos).
DEMO_EMAIL = "demo@afk.agency"
DEMO_PASSWORD = "DemoSession1"
DEMO_ORG_NAME = "Meridian Growth Co."
DEMO_USER_NAME = "Jordan Lee (Founder)"


def ensure_demo_session(session: Session) -> User:
    """Idempotently provision demo org, user, and a completed Revenue Audit."""
    user = session.exec(select(User).where(User.email == DEMO_EMAIL)).first()
    if user:
        seed_demo_audit(session, user.organization_id)
        return user

    org = Organization(name=DEMO_ORG_NAME)
    session.add(org)
    session.flush()

    user = User(
        email=DEMO_EMAIL,
        full_name=DEMO_USER_NAME,
        hashed_password=get_password_hash(DEMO_PASSWORD),
        role=UserRole.ADMIN,
        organization_id=org.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    seed_demo_audit(session, user.organization_id)
    return user


def seed_demo_audit(session, org_id: int):
    """Seed a realistic completed Revenue Audit for the demo organization.
    All UI numbers derive from these answers via the constraint engine."""
    import json as _json
    from backend.app.models.intelligence import RevenueAudit
    from sqlmodel import select as _select
    existing = session.exec(_select(RevenueAudit).where(RevenueAudit.organization_id == org_id)).first()
    if existing:
        return
    demo_answers = {
        "business_type": "B2B services / agency",
        "industry": "Growth consulting for D2C brands",
        "team_size": 6,
        "growth_stage": "Early revenue (finding repeatability)",
        "monthly_revenue": 850000,
        "revenue_model": "Mixed",
        "avg_deal_value": 150000,
        "revenue_goal_12m": 2500000,
        "leads_per_month": 14,
        "lead_sources_count": "One",
        "primary_lead_source": "Referrals / word of mouth",
        "marketing_active": "Sporadic",
        "qualification_process": "Informal gut-feel",
        "pct_leads_worth_it": 40,
        "conversion_close_rate": 22,
        "conversion_followups": "2",
        "conversion_owner": "Founder leads most deals",
        "conversion_process": "Mostly in people's heads",
        "conversion_cycle_days": 35,
        "pricing_confidence": "Probably underpriced",
        "last_price_change": "Never",
        "discounting": "Sometimes",
        "repeat_rate": 45,
        "churn_reason_known": "Partially / anecdotally",
        "retention_process": "Ad-hoc",
        "founder_in_every_sale": "Yes, every deal",
        "documented_sales_process": "No",
        "self_diagnosis": "We need more leads. Referrals are unpredictable.",
        "biggest_worry": "If two clients leave in the same month we are in trouble.",
    }
    session.add(RevenueAudit(organization_id=org_id, answers_json=_json.dumps(demo_answers)))
    session.commit()

def seed_data():
    from backend.app.core.settings import get_settings
    init_db()
    if not get_settings().seed_demo:
        print("[*] Demo seed disabled (AFK_SEED_DEMO=false). Register to create your organisation.")
        return
    with Session(engine) as session:
        # Check if already seeded
        existing_org = session.exec(select(Organization)).first()
        if existing_org:
            print("[*] Database already contains data. Skipping seeding.")
            return

        print("[*] Seeding database with demo data (AFK_SEED_DEMO=true)...")

        # 1. Create Organization
        org = Organization(name="AFK Growth Agency")
        session.add(org)
        session.commit()
        session.refresh(org)

        # 2. Create Users
        hashed_pw = get_password_hash("password123")
        
        admin = User(
            email="admin@afk.agency",
            full_name="Alex Mercer (CTO)",
            hashed_password=hashed_pw,
            role=UserRole.ADMIN,
            organization_id=org.id
        )
        team = User(
            email="team@afk.agency",
            full_name="Sarah Connor (Growth Hacker)",
            hashed_password=hashed_pw,
            role=UserRole.TEAM,
            organization_id=org.id
        )
        client_user = User(
            email="client@acme.com",
            full_name="John Doe (CEO, Acme Corp)",
            hashed_password=hashed_pw,
            role=UserRole.CLIENT,
            organization_id=org.id
        )
        
        session.add_all([admin, team, client_user])
        session.commit()
        session.refresh(admin)
        session.refresh(team)
        session.refresh(client_user)

        # 3. Create CRM Clients / Leads
        c1 = Client(
            name="John Doe",
            email="john@acme.com",
            company="Acme Corp",
            phone="+1 (555) 019-2834",
            status=ClientStatus.ACTIVE,
            pipeline_stage=PipelineStage.WON,
            organization_id=org.id
        )
        c2 = Client(
            name="Bruce Wayne",
            email="bruce@wayne.corp",
            company="Wayne Enterprises",
            phone="+1 (555) 999-1111",
            status=ClientStatus.LEAD,
            pipeline_stage=PipelineStage.PROPOSAL,
            organization_id=org.id
        )
        c3 = Client(
            name="Tony Stark",
            email="tony@stark.industries",
            company="Stark Industries",
            phone="+1 (555) 300-4000",
            status=ClientStatus.LEAD,
            pipeline_stage=PipelineStage.QUALIFIED,
            organization_id=org.id
        )
        c4 = Client(
            name="Sarah Connor",
            email="sarah@cyberdyne.io",
            company="Cyberdyne Systems",
            phone="+1 (555) 800-1997",
            status=ClientStatus.LEAD,
            pipeline_stage=PipelineStage.CONTACT,
            organization_id=org.id
        )
        
        session.add_all([c1, c2, c3, c4])
        session.commit()
        session.refresh(c1)
        session.refresh(c2)
        session.refresh(c3)

        # Add Notes to Clients
        n1 = ClientNote(
            content="Interested in scaling LinkedIn outbound and automated newsletter scheduling.",
            client_id=c1.id
        )
        n2 = ClientNote(
            content="Sent enterprise proposal for full funnel inbound lead qualification. Review expected by Friday.",
            client_id=c2.id
        )
        session.add_all([n1, n2])

        # 4. Create Projects
        p1 = Project(
            name="Q3 Growth Campaign",
            description="Scaling lead acquisition, content orchestration and cold outreach pipelines.",
            status=ProjectStatus.ACTIVE,
            due_date=datetime.utcnow() + timedelta(days=45),
            organization_id=org.id
        )
        p2 = Project(
            name="Stark AI Lead Qualifier",
            description="Developing dynamic workflows to qualify high ticket inbound leads using LLMs.",
            status=ProjectStatus.PLANNING,
            due_date=datetime.utcnow() + timedelta(days=90),
            organization_id=org.id
        )
        session.add_all([p1, p2])
        session.commit()
        session.refresh(p1)
        session.refresh(p2)

        # 5. Create Kanban Tasks
        t1 = Task(
            title="Configure Inbound Lead Funnel",
            description="Define stages and mapping rules from Webflow contact forms into CRM pipeline.",
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
            column_index=0,
            due_date=datetime.utcnow() - timedelta(days=2),
            project_id=p1.id,
            assignee_id=admin.id
        )
        t2 = Task(
            title="Draft cold outreach templates",
            description="Write 3-sequence email variants focusing on growth performance. Target VCs & Founders.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            column_index=0,
            due_date=datetime.utcnow() + timedelta(days=5),
            project_id=p1.id,
            assignee_id=team.id
        )
        t3 = Task(
            title="Design landing page variation",
            description="Design dark-mode variant high conversion value page aiming to capture contact emails.",
            status=TaskStatus.REVIEW,
            priority=TaskPriority.HIGH,
            column_index=0,
            due_date=datetime.utcnow() + timedelta(days=1),
            project_id=p1.id,
            assignee_id=team.id
        )
        t4 = Task(
            title="Integrate email automation tool",
            description="Establish automated SMTP and API sequences connecting lead triggers directly to inbox.",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            column_index=0,
            due_date=datetime.utcnow() + timedelta(days=12),
            project_id=p1.id,
            assignee_id=admin.id
        )
        
        session.add_all([t1, t2, t3, t4])
        
        # 6. Create AI Conversations
        conv = AIConversation(
            title="Marketing Strategy for Acme Corp",
            assistant_type=AIAssistantType.MARKETING_STRATEGIST,
            user_id=admin.id
        )
        session.add(conv)
        session.commit()
        session.refresh(conv)
        
        m_user = AIMessage(
            role="user",
            content="Can you suggest a weekly content posting strategy for a B2B agency on LinkedIn?",
            conversation_id=conv.id
        )
        m_assistant = AIMessage(
            role="assistant",
            content="Here is a high-performing 5-day content strategy for B2B LinkedIn:\n\n1. **Monday (Authority/Proof)**: Case study or metrics-focused walkthrough explaining how you solved a bottleneck.\n2. **Tuesday (Educational)**: A step-by-step tutorial checklist on solving a common problem (e.g., 'How we build automated qualified funnels').\n3. **Wednesday (Opinion/Perspective)**: A contrarian take on a standard marketing myth to prompt conversation.\n4. **Thursday (Storytelling)**: A personal founder story sharing a failure and the lesson learned.\n5. **Friday (Call to Action/Lightweight)**: A resource giveaway (e.g., a free database sheet or PDF checklist) prompting users to comment.",
            conversation_id=conv.id
        )
        session.add_all([m_user, m_assistant])

        # 7. Create Generated Content
        gc = GeneratedContent(
            title="B2B AI Automation Hooks",
            content="1. 'Most founders waste 10 hours a week on unqualified calls. Here is how we automated qualification in 3 steps.'\n2. 'Stop using generic cold emails. We used dynamic AI context mapping and tripled our response rates.'",
            channel=ContentChannel.LINKEDIN,
            creator_id=admin.id
        )
        session.add(gc)

        # 8. Create Invoices
        inv1 = Invoice(
            invoice_number="INV-2026-001",
            amount=4500.0,
            status=InvoiceStatus.PAID,
            due_date=datetime.utcnow() - timedelta(days=5),
            client_id=c1.id
        )
        inv2 = Invoice(
            invoice_number="INV-2026-002",
            amount=2800.0,
            status=InvoiceStatus.SENT,
            due_date=datetime.utcnow() + timedelta(days=15),
            client_id=c1.id
        )
        session.add_all([inv1, inv2])

        # 9. Create Active Workflow
        steps = [
            {"id": "step_1", "type": "trigger", "name": "Lead Form Submission", "config": {"source": "website_contact"}},
            {"id": "step_2", "type": "action_ai", "name": "AI Qualify Company", "config": {"prompt": "Check if company size is > 50 and funded."}},
            {"id": "step_3", "type": "action_email", "name": "Send Sequence A/B", "config": {"template": "welcome_premium"}},
            {"id": "step_4", "type": "action_crm", "name": "Upsert CRM Lead", "config": {"stage": "qualified"}},
            {"id": "step_5", "type": "action_slack", "name": "Post to #growth", "config": {"webhook": "https://hooks.slack.com/services/..."}}
        ]
        
        w = Workflow(
            name="Inbound Lead qualification & onboarding",
            description="Qualifies high-tier companies instantly via AI and alerts the growth channel on Slack.",
            steps_json=json.dumps(steps),
            is_active=True,
            organization_id=org.id
        )
        session.add(w)
        
        session.commit()
        seed_demo_audit(session, 1)
    print("[+] Seeding database completed successfully.")

if __name__ == "__main__":
    seed_data()

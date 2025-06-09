"""
Hunter Agency V2.2 - Async Production Email Engine
Transformed from V2.0 with full async architecture
"""

# Fix pour éviter les métriques Prometheus dupliquées
from prometheus_client import REGISTRY
try:
    collectors_to_remove = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        collectors_to_remove.append(collector)
    
    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except KeyError:
            pass
except:
    pass

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import structlog
import httpx
from contextlib import asynccontextmanager

# FastAPI & Pydantic
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# Database
import aiosqlite
from databases import Database

# Scheduling
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Monitoring
from prometheus_client import Counter, Histogram, Gauge

# Routers
from ai.lead_intelligence.router import router as lead_intelligence_router
from crm.email_engine.router import router as email_engine_router
from crm.smart_pipeline.api.routes import router as smart_pipeline_router
from automation.social_automation.router import router as social_automation_router
from billing.revenue_automation.router import router as billing_router

load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# ========================
# CONFIGURATION
# ========================

DATABASE_URL = "sqlite+aiosqlite:///./hunter_agency.db"
database = Database(DATABASE_URL)

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', 'contact@hunter-agency.com')

# ========================
# METRICS (avec protection contre les doublons)
# ========================

try:
    email_counter = Counter('emails_sent_total', 'Total emails sent', ['sequence_type', 'status'])
    email_duration = Histogram('email_send_duration_seconds', 'Email send duration')
    sequence_gauge = Gauge('active_sequences_total', 'Active sequences count')
    lead_counter = Counter('leads_created_total', 'Total leads created', ['source', 'grade_tier'])
except ValueError as e:
    # Si les métriques existent déjà, les récupérer
    logger.warning("Metrics already exist, reusing them", error=str(e))
    for collector in REGISTRY._collector_to_names:
        if hasattr(collector, '_name'):
            if collector._name == 'emails_sent_total':
                email_counter = collector
            elif collector._name == 'email_send_duration_seconds':
                email_duration = collector
            elif collector._name == 'active_sequences_total':
                sequence_gauge = collector
            elif collector._name == 'leads_created_total':
                lead_counter = collector

# ========================
# DATABASE SETUP
# ========================

async def create_tables():
    """Create database tables with async"""
    async with aiosqlite.connect("hunter_agency.db") as db:
        # Enable optimizations
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=10000")
        
        # Leads table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                industry TEXT,
                source TEXT,
                grade INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact TIMESTAMP
            )
        """)
        
        # Email campaigns table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                template_type TEXT,
                subject TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                loom_video_id TEXT,
                sequence_id INTEGER,
                sequence_step INTEGER,
                status TEXT DEFAULT 'sent',
                sendgrid_message_id TEXT,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                replied_at TIMESTAMP,
                bounce_reason TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)
        
        # Email sequences table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS email_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                sequence_type TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sequence steps table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sequence_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER,
                step_number INTEGER,
                delay_days INTEGER,
                delay_hours INTEGER DEFAULT 0,
                subject_template TEXT,
                email_template TEXT,
                loom_video_id TEXT,
                trigger_condition TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (sequence_id) REFERENCES email_sequences (id)
            )
        """)
        
        # Lead sequences tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lead_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                sequence_id INTEGER,
                current_step INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                paused_at TIMESTAMP,
                next_send_at TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id),
                FOREIGN KEY (sequence_id) REFERENCES email_sequences (id)
            )
        """)
        
        # Performance indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_message_id ON email_campaigns(sendgrid_message_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_lead_sequences_next_send ON lead_sequences(next_send_at)")
        
        await db.commit()
        logger.info("Database tables created successfully")

# ========================
# MODELS
# ========================

class Lead(BaseModel):
    email: EmailStr
    first_name: str
    industry: Optional[str] = "business"
    source: Optional[str] = "manual"

class WebhookEvent(BaseModel):
    email: str
    event: str
    timestamp: int
    sg_message_id: Optional[str] = None

# ========================
# ASYNC SENDGRID CLIENT
# ========================

class AsyncSendGridClient:
    """Async SendGrid client with retry logic"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sendgrid.com/v3"
        
    async def send_email(self, to_email: str, subject: str, html_content: str, 
                        from_email: str = None) -> Dict:
        """Send email async with retry logic"""
        if not from_email:
            from_email = SENDGRID_FROM_EMAIL
            
        payload = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "subject": subject
            }],
            "from": {"email": from_email},
            "content": [{
                "type": "text/html",
                "value": html_content
            }]
        }
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(3):
                try:
                    with email_duration.time():
                        response = await client.post(
                            f"{self.base_url}/mail/send",
                            json=payload,
                            headers=headers
                        )
                    
                    if response.status_code == 202:
                        message_id = response.headers.get('X-Message-Id')
                        logger.info("Email sent successfully", 
                                  to_email=to_email, message_id=message_id)
                        email_counter.labels(sequence_type='unknown', status='sent').inc()
                        return {"status": "sent", "message_id": message_id}
                    
                    elif response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning("Rate limited, retrying", 
                                     attempt=attempt, wait_time=wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        logger.error("SendGrid error", 
                                   status_code=response.status_code,
                                   response=response.text)
                        email_counter.labels(sequence_type='unknown', status='failed').inc()
                        return {"status": "failed", "error": response.text}
                        
                except Exception as e:
                    logger.error("Email send exception", error=str(e), attempt=attempt)
                    if attempt == 2:
                        email_counter.labels(sequence_type='unknown', status='error').inc()
                        return {"status": "error", "error": str(e)}
                    await asyncio.sleep(2 ** attempt)
        
        return {"status": "failed", "error": "Max retries exceeded"}

# ========================
# BUSINESS LOGIC
# ========================

def grade_lead(lead: Lead) -> int:
    """Enhanced lead grading"""
    score = 50
    
    # Industry scoring
    high_value_industries = ["saas", "ecommerce", "agency", "consulting", "fintech"]
    if lead.industry and lead.industry.lower() in high_value_industries:
        score += 25
    
    # Source scoring
    source_scores = {
        "linkedin": 20,
        "referral": 25,
        "inbound": 20,
        "webinar": 15,
        "manual": 5
    }
    score += source_scores.get(lead.source.lower(), 0)
    
    # Email domain scoring
    domain = lead.email.split('@')[1].lower()
    free_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    if domain not in free_domains:
        score += 15
    
    return min(100, max(0, score))

async def create_lead_async(lead_data: Lead) -> Dict:
    """Create lead with async database operations"""
    grade = grade_lead(lead_data)
    grade_tier = "high" if grade >= 70 else "medium" if grade >= 50 else "low"
    
    try:
        # Use database connection pool
        lead_id = await database.fetch_val("""
            INSERT INTO leads (email, first_name, industry, source, grade)
            VALUES (:email, :first_name, :industry, :source, :grade)
            RETURNING id
        """, {
            "email": lead_data.email,
            "first_name": lead_data.first_name,
            "industry": lead_data.industry,
            "source": lead_data.source,
            "grade": grade
        })
        
        lead_counter.labels(source=lead_data.source, grade_tier=grade_tier).inc()
        logger.info("Lead created", lead_id=lead_id, email=lead_data.email, grade=grade)
        
        return {"lead_id": lead_id, "grade": grade, "grade_tier": grade_tier}
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Lead already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_email_template(template_name: str, lead_data: dict, loom_id: str = None):
    """Get email template (simplified version)"""
    first_name = lead_data.get('first_name', 'there')
    industry = lead_data.get('industry', 'business')
    
    templates = {
        "cold_outreach_step1": f"""
        <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white;">🔥 Hunter Agency V2.2</h1>
            </div>
            <div style="padding: 30px;">
                <p>Hey <strong>{first_name}</strong>! 👋</p>
                <p>I noticed you're in {industry} and wanted to reach out.</p>
                <p>I help {industry} businesses scale their lead generation with automation.</p>
                <p><strong>Quick question:</strong> What's your biggest challenge with lead generation right now?</p>
                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://calendly.com/hunter-agency" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">📅 Quick Chat</a>
                </div>
                <p>Best,<br>Hunter Agency V2.2 Team</p>
            </div>
        </body></html>""",
        
        "nurturing_step1": f"""
        <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white;">🎉 Welcome {first_name}!</h1>
            </div>
            <div style="padding: 30px;">
                <p>Thanks for your interest in {industry} automation!</p>
                <p>Here's what happens next:</p>
                <ol>
                    <li>We'll analyze your current setup</li>
                    <li>Create a custom strategy</li>
                    <li>Implement and optimize</li>
                </ol>
                <p>I'll send you a detailed plan in the next 48 hours.</p>
                <p>Best,<br>Hunter Agency V2.2 Team</p>
            </div>
        </body></html>"""
    }
    
    return templates.get(template_name, templates["cold_outreach_step1"])

# ========================
# SEQUENCE PROCESSOR
# ========================

class AsyncSequenceProcessor:
    """Async sequence processor using APScheduler"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def start(self):
        """Start the async sequence processor"""
        self.scheduler.add_job(
            self.process_pending_sequences,
            IntervalTrigger(minutes=5),
            id='sequence_processor',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Async sequence processor started")
    
    async def stop(self):
        """Stop the sequence processor"""
        self.scheduler.shutdown(wait=False)
        logger.info("Sequence processor stopped")
    
    async def process_pending_sequences(self):
        """Process all pending sequence emails"""
        try:
            now = datetime.now()
            
            # Get pending sequences with async query
            pending = await database.fetch_all("""
                SELECT ls.id, ls.lead_id, ls.sequence_id, ls.current_step, l.email, l.first_name, l.industry
                FROM lead_sequences ls
                JOIN leads l ON ls.lead_id = l.id
                WHERE ls.status = 'active' 
                AND ls.next_send_at IS NOT NULL 
                AND ls.next_send_at <= :now
                LIMIT 50
            """, {"now": now})
            
            if pending:
                logger.info("Processing pending sequences", count=len(pending))
                
                # Process sequences async
                for sequence_data in pending:
                    try:
                        await self.send_sequence_email(sequence_data)
                        await asyncio.sleep(1)  # Rate limiting
                    except Exception as e:
                        logger.error("Error processing sequence", 
                                   sequence_id=sequence_data['id'], error=str(e))
            
            # Update metrics
            active_count = await database.fetch_val(
                "SELECT COUNT(*) FROM lead_sequences WHERE status = 'active'"
            )
            sequence_gauge.set(active_count or 0)
            
        except Exception as e:
            logger.error("Sequence processor error", error=str(e))
    
    async def send_sequence_email(self, sequence_data: Dict):
        """Send individual sequence email async"""
        lead_id = sequence_data['lead_id']
        email = sequence_data['email']
        first_name = sequence_data['first_name']
        industry = sequence_data['industry']
        current_step = sequence_data['current_step']
        next_step = current_step + 1
        
        # Prepare lead data for template
        lead_data = {
            'first_name': first_name,
            'industry': industry,
            'email': email
        }
        
        # Get template based on step
        template_name = "cold_outreach_step1" if next_step == 1 else "nurturing_step1"
        subject = f"Quick question about {industry}, {first_name}" if next_step == 1 else f"Welcome to Hunter Agency, {first_name}!"
        html_content = get_email_template(template_name, lead_data)
        
        # Send email
        if SENDGRID_API_KEY:
            client = AsyncSendGridClient(SENDGRID_API_KEY)
            result = await client.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
        else:
            result = {"status": "sent", "message_id": f"test_{datetime.now().timestamp()}"}
            logger.info("Email sent (test mode - no SendGrid API key)", to_email=email)
        
        # Log result
        await database.execute("""
            INSERT INTO email_campaigns (lead_id, template_type, subject, sendgrid_message_id, status, sequence_id, sequence_step)
            VALUES (:lead_id, :template_type, :subject, :msg_id, :status, :sequence_id, :step)
        """, {
            "lead_id": lead_id,
            "template_type": template_name,
            "subject": subject,
            "msg_id": result.get('message_id'),
            "status": result['status'],
            "sequence_id": sequence_data['sequence_id'],
            "step": next_step
        })
        
        # Update sequence progress
        if result['status'] == 'sent':
            # Calculate next send time (3 days later for next step)
            next_send = datetime.now() + timedelta(days=3)
            
            await database.execute("""
                UPDATE lead_sequences 
                SET current_step = :step, next_send_at = :next_send
                WHERE id = :id
            """, {
                "id": sequence_data['id'],
                "step": next_step,
                "next_send": next_send if next_step < 5 else None  # Stop after 5 steps
            })
            
            if next_step >= 5:
                await database.execute("""
                    UPDATE lead_sequences 
                    SET status = 'completed', completed_at = :now
                    WHERE id = :id
                """, {"id": sequence_data['id'], "now": datetime.now()})

# ========================
# SEQUENCE TEMPLATES SETUP
# ========================

async def create_default_sequences():
    """Create default email sequences"""
    sequences = [
        {
            "name": "Cold Outreach Sequence",
            "description": "5-step cold outreach for new leads",
            "sequence_type": "cold_outreach"
        },
        {
            "name": "Lead Nurturing Sequence", 
            "description": "3-step nurturing for engaged leads",
            "sequence_type": "nurturing"
        }
    ]
    
    for seq_data in sequences:
        try:
            await database.execute("""
                INSERT OR IGNORE INTO email_sequences (name, description, sequence_type)
                VALUES (:name, :description, :sequence_type)
            """, seq_data)
        except Exception as e:
            logger.error("Error creating sequence", sequence=seq_data['name'], error=str(e))
    
    logger.info("Default sequences created")

# ========================
# LIFESPAN MANAGEMENT
# ========================

sequence_processor = AsyncSequenceProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Hunter Agency V2.2 Async...")
    await database.connect()
    await create_tables()
    await create_default_sequences()
    await sequence_processor.start()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await sequence_processor.stop()
    await database.disconnect()
    logger.info("Application shutdown complete")

# ========================
# FASTAPI APP
# ========================

app = FastAPI(
    title="Hunter Agency V2.2 - Async Email Engine",
    description="Production-ready async email sequences",
    version="2.2.0",
    lifespan=lifespan
)

# Mount routers
app.include_router(lead_intelligence_router, prefix="/ai/lead_intelligence")
app.include_router(email_engine_router, prefix="/crm/email_engine")
app.include_router(smart_pipeline_router, prefix="/crm/smart_pipeline")
app.include_router(social_automation_router, prefix="/automation/social_automation")
app.include_router(billing_router, prefix="/billing")

# ========================
# API ENDPOINTS
# ========================

@app.get("/health")
async def health_check():
    """Async health check"""
    try:
        await database.fetch_val("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "OK",
        "service": "Hunter Agency V2.2 Async",
        "version": "2.2.0",
        "database": db_status,
        "scheduler": "running" if sequence_processor.scheduler.running else "stopped"
    }

@app.post("/leads")
async def create_lead_endpoint(lead: Lead):
    """Create lead async and trigger sequence"""
    result = await create_lead_async(lead)
    
    # Determine sequence type
    sequence_type = "nurturing" if result["grade"] >= 70 else "cold_outreach"
    
    # Get sequence ID
    sequence = await database.fetch_one("""
        SELECT id FROM email_sequences 
        WHERE sequence_type = :type AND is_active = 1
        LIMIT 1
    """, {"type": sequence_type})
    
    if sequence:
        # Add to sequence
        await database.execute("""
            INSERT OR IGNORE INTO lead_sequences (lead_id, sequence_id, next_send_at)
            VALUES (:lead_id, :sequence_id, :next_send)
        """, {
            "lead_id": result["lead_id"],
            "sequence_id": sequence["id"],
            "next_send": datetime.now()  # Send first email immediately
        })
    
    return {
        "message": "Lead created and sequence triggered",
        "lead": result,
        "sequence_type": sequence_type
    }

@app.get("/sequences/analytics")
async def get_sequence_analytics():
    """Get async sequence analytics"""
    # Active sequences
    active_sequences = await database.fetch_val(
        "SELECT COUNT(*) FROM lead_sequences WHERE status = 'active'"
    ) or 0
    
    # Completed sequences
    completed_sequences = await database.fetch_val(
        "SELECT COUNT(*) FROM lead_sequences WHERE status = 'completed'"
    ) or 0
    
    # Email performance
    email_stats = await database.fetch_one("""
        SELECT 
            COUNT(*) as total_sent,
            COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as total_opens,
            COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as total_clicks
        FROM email_campaigns 
        WHERE sent_at >= datetime('now', '-30 days')
    """)
    
    total_sent = email_stats["total_sent"] if email_stats else 0
    total_opens = email_stats["total_opens"] if email_stats else 0
    total_clicks = email_stats["total_clicks"] if email_stats else 0
    
    return {
        "overview": {
            "active_sequences": active_sequences,
            "completed_sequences": completed_sequences,
            "completion_rate": f"{(completed_sequences/(active_sequences+completed_sequences)*100):.1f}%" if (active_sequences+completed_sequences) > 0 else "0%"
        },
        "email_performance": {
            "total_sent": total_sent,
            "open_rate": f"{(total_opens/total_sent*100):.1f}%" if total_sent > 0 else "0%",
            "click_rate": f"{(total_clicks/total_sent*100):.1f}%" if total_sent > 0 else "0%"
        }
    }

@app.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(events: List[WebhookEvent]):
    """Handle SendGrid webhook events async"""
    for event in events:
        try:
            # Find campaign by message ID or email
            if event.sg_message_id:
                campaign = await database.fetch_one("""
                    SELECT id FROM email_campaigns 
                    WHERE sendgrid_message_id = :msg_id
                """, {"msg_id": event.sg_message_id})
            else:
                # Fallback: find by email (most recent)
                campaign = await database.fetch_one("""
                    SELECT ec.id FROM email_campaigns ec
                    JOIN leads l ON ec.lead_id = l.id
                    WHERE l.email = :email
                    ORDER BY ec.sent_at DESC LIMIT 1
                """, {"email": event.email})
            
            if not campaign:
                continue
            
            # Update campaign based on event type
            if event.event == "open":
                await database.execute("""
                    UPDATE email_campaigns 
                    SET opened_at = :timestamp, status = 'opened'
                    WHERE id = :campaign_id AND opened_at IS NULL
                """, {
                    "timestamp": datetime.fromtimestamp(event.timestamp),
                    "campaign_id": campaign["id"]
                })
                
            elif event.event == "click":
                await database.execute("""
                    UPDATE email_campaigns 
                    SET clicked_at = :timestamp, status = 'clicked'
                    WHERE id = :campaign_id AND clicked_at IS NULL
                """, {
                    "timestamp": datetime.fromtimestamp(event.timestamp),
                    "campaign_id": campaign["id"]
                })
                
            elif event.event in ["bounce", "blocked", "dropped"]:
                await database.execute("""
                    UPDATE email_campaigns 
                    SET status = :status, bounce_reason = :reason
                    WHERE id = :campaign_id
                """, {
                    "status": event.event,
                    "reason": f"SendGrid {event.event} event",
                    "campaign_id": campaign["id"]
                })
                
                # Mark lead as invalid
                await database.execute("""
                    UPDATE leads 
                    SET status = 'invalid'
                    WHERE email = :email
                """, {"email": event.email})
                
            logger.info("Webhook processed", event=event.event, email=event.email)
        
        except Exception as e:
            logger.error("Webhook processing error", event=event.dict(), error=str(e))
    
    return {"status": "processed", "events": len(events)}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hunter Agency V2.2 - Async Email Engine",
        "version": "2.2.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "create_lead": "/leads",
            "analytics": "/sequences/analytics",
            "webhook": "/webhooks/sendgrid"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
    



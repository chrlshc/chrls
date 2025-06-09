"""
Hunter Agency V2.2 - Async Production Email Engine
Transformed from V2.0 with full async architecture
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import structlog
import httpx
from contextlib import asynccontextmanager

# FastAPI & Pydantic
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr

# Database
import aiosqlite
from databases import Database

# Scheduling
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Monitoring
from prometheus_client import Counter, Histogram, Gauge

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
# METRICS
# ========================

email_counter = Counter('emails_sent_total', 'Total emails sent', ['sequence_type', 'status'])
email_duration = Histogram('email_send_duration_seconds', 'Email send duration')
sequence_gauge = Gauge('active_sequences_total', 'Active sequences count')
lead_counter = Counter('leads_created_total', 'Total leads created', ['source', 'grade_tier'])

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
    """Enhanced lead grading with async support"""
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
                SELECT ls.id, ls.lead_id, ls.sequence_id, ls.current_step, l.email, l.first_name
                FROM lead_sequences ls
                JOIN leads l ON ls.lead_id = l.id
                WHERE ls.status = 'active' 
                AND ls.next_send_at IS NOT NULL 
                AND ls.next_send_at <= :now
                LIMIT 50
            """, {"now": now})
            
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
            sequence_gauge.set(active_count)
            
        except Exception as e:
            logger.error("Sequence processor error", error=str(e))
    
    async def send_sequence_email(self, sequence_data: Dict):
        """Send individual sequence email async"""
        # Simplified version - you can expand this
        lead_id = sequence_data['lead_id']
        email = sequence_data['email']
        first_name = sequence_data['first_name']
        
        # Send email
        client = AsyncSendGridClient(SENDGRID_API_KEY)
        result = await client.send_email(
            to_email=email,
            subject=f"Hello {first_name}!",
            html_content=f"<h1>Hi {first_name}!</h1><p>This is a test email from Hunter Agency V2.2 Async!</p>"
        )
        
        # Log result
        await database.execute("""
            INSERT INTO email_campaigns (lead_id, subject, sendgrid_message_id, status)
            VALUES (:lead_id, :subject, :msg_id, :status)
        """, {
            "lead_id": lead_id,
            "subject": f"Hello {first_name}!",
            "msg_id": result.get('message_id'),
            "status": result['status']
        })

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
    
    # Add to sequence (simplified)
    await database.execute("""
        INSERT INTO lead_sequences (lead_id, sequence_id, next_send_at)
        VALUES (:lead_id, 1, :next_send)
    """, {
        "lead_id": result["lead_id"],
        "next_send": datetime.now()
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
    )
    
    # Email performance
    email_stats = await database.fetch_one("""
        SELECT 
            COUNT(*) as total_sent,
            COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as total_opens
        FROM email_campaigns 
        WHERE sent_at >= datetime('now', '-30 days')
    """)
    
    return {
        "overview": {
            "active_sequences": active_sequences,
            "total_sent": email_stats["total_sent"] if email_stats else 0,
            "open_rate": f"{(email_stats['total_opens']/email_stats['total_sent']*100):.1f}%" if email_stats and email_stats["total_sent"] > 0 else "0%"
        }
    }

@app.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(events: List[WebhookEvent]):
    """Handle SendGrid webhook events async"""
    for event in events:
        try:
            # Update campaign based on event type
            if event.event == "open":
                await database.execute("""
                    UPDATE email_campaigns 
                    SET opened_at = :timestamp
                    WHERE sendgrid_message_id = :msg_id AND opened_at IS NULL
                """, {
                    "timestamp": datetime.fromtimestamp(event.timestamp),
                    "msg_id": event.sg_message_id
                })
                
            logger.info("Webhook processed", event=event.event, email=event.email)
        
        except Exception as e:
            logger.error("Webhook processing error", event=event.dict(), error=str(e))
    
    return {"status": "processed", "events": len(events)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

#!/usr/bin/env python3
"""
🌐 HUNTER AGENCY - Email Engine API
FastAPI interface for email campaign management & automation
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio
from pydantic import BaseModel, EmailStr

# Import our models and services
from .models import (
    EmailTemplate, EmailSequence, SequenceStep, Email, EmailCampaign,
    SequenceEnrollment, LoomVideo, EmailTemplateCreate, EmailTemplateUpdate, 
    EmailTemplateResponse, EmailSequenceCreate, EmailSequenceResponse,
    LoomVideoCreate, LoomVideoResponse, EmailMetrics, CampaignPerformance,
    EmailStatus, SequenceStatus, CampaignType, TriggerType
)
from .template_engine import EmailTemplateEngine, LoomService
from .sequence_automation import SequenceAutomationEngine, SequenceManager
from .sequence_automation import trigger_sequence_for_lead, process_sequences

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 🚀 FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="📧 Hunter Agency - Email Engine",
    description="Advanced email automation with Loom integration & mass personalization",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency (integrate with your existing DB)
def get_db():
    # Mock database - replace with real SQLAlchemy session
    from unittest.mock import Mock
    return Mock()

# ============================================================================
# 📧 EMAIL TEMPLATE ENDPOINTS
# ============================================================================

@app.post("/templates", response_model=EmailTemplateResponse, status_code=201)
async def create_template(
    template: EmailTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create new email template"""
    try:
        # Generate slug if not provided
        if not template.slug:
            template.slug = template.name.lower().replace(' ', '_').replace('-', '_')
        
        # Validate template syntax
        template_engine = EmailTemplateEngine()
        validation = template_engine.validate_template(template.html_template)
        
        if not validation['valid']:
            raise HTTPException(
                status_code=400, 
                detail=f"Template validation failed: {validation['error']}"
            )
        
        # Create template
        db_template = EmailTemplate(**template.dict())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        logger.info(f"✅ Created template {db_template.id}: {template.name}")
        
        return EmailTemplateResponse.from_orm(db_template)
        
    except Exception as e:
        logger.error(f"❌ Failed to create template: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/templates", response_model=List[EmailTemplateResponse])
async def get_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get email templates with filtering"""
    try:
        query = db.query(EmailTemplate)
        
        # Apply filters
        if active_only:
            query = query.filter(EmailTemplate.is_active == True)
        if category:
            query = query.filter(EmailTemplate.category == category)
        if search:
            query = query.filter(
                db.or_(
                    EmailTemplate.name.ilike(f"%{search}%"),
                    EmailTemplate.subject_template.ilike(f"%{search}%")
                )
            )
        
        templates = query.offset(skip).limit(limit).all()
        return [EmailTemplateResponse.from_orm(t) for t in templates]
        
    except Exception as e:
        logger.error(f"❌ Failed to get templates: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get specific template"""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return EmailTemplateResponse.from_orm(template)

@app.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: int,
    template_update: EmailTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update email template"""
    db_template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Validate template if HTML is being updated
    if template_update.html_template:
        template_engine = EmailTemplateEngine()
        validation = template_engine.validate_template(template_update.html_template)
        
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Template validation failed: {validation['error']}"
            )
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db_template.updated_at = datetime.utcnow()
    db.commit()
    
    return EmailTemplateResponse.from_orm(db_template)

@app.post("/templates/{template_id}/preview", response_class=HTMLResponse)
async def preview_template(
    template_id: int,
    merge_data: Dict[str, Any] = Body(...),
    loom_video_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Preview template with sample data"""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        template_engine = EmailTemplateEngine()
        
        rendered_html, tracking_data = template_engine.render_template(
            template_content=template.html_template,
            merge_data=merge_data,
            loom_video_id=loom_video_id or template.loom_video_id,
            lead_id=999,  # Mock ID for preview
            email_id=999
        )
        
        return HTMLResponse(content=rendered_html)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preview failed: {str(e)}")

# ============================================================================
# ⚡ EMAIL SEQUENCE ENDPOINTS
# ============================================================================

@app.post("/sequences", response_model=EmailSequenceResponse, status_code=201)
async def create_sequence(
    sequence: EmailSequenceCreate,
    db: Session = Depends(get_db)
):
    """Create new email sequence"""
    try:
        # Generate slug if not provided
        if not sequence.slug:
            sequence.slug = sequence.name.lower().replace(' ', '_').replace('-', '_')
        
        # Create sequence
        db_sequence = EmailSequence(**sequence.dict())
        db.add(db_sequence)
        db.commit()
        db.refresh(db_sequence)
        
        logger.info(f"✅ Created sequence {db_sequence.id}: {sequence.name}")
        
        return EmailSequenceResponse.from_orm(db_sequence)
        
    except Exception as e:
        logger.error(f"❌ Failed to create sequence: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sequences", response_model=List[EmailSequenceResponse])
async def get_sequences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    campaign_type: Optional[CampaignType] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get email sequences"""
    try:
        query = db.query(EmailSequence)
        
        if active_only:
            query = query.filter(EmailSequence.is_active == True)
        if campaign_type:
            query = query.filter(EmailSequence.campaign_type == campaign_type)
        
        sequences = query.offset(skip).limit(limit).all()
        return [EmailSequenceResponse.from_orm(s) for s in sequences]
        
    except Exception as e:
        logger.error(f"❌ Failed to get sequences: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sequences/{sequence_id}/steps")
async def add_sequence_step(
    sequence_id: int,
    step_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Add step to email sequence"""
    sequence = db.query(EmailSequence).filter(EmailSequence.id == sequence_id).first()
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    try:
        step = SequenceStep(
            sequence_id=sequence_id,
            **step_data
        )
        
        db.add(step)
        db.commit()
        
        return {"message": f"Step added to sequence {sequence_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sequences/{sequence_id}/enroll")
async def enroll_leads_in_sequence(
    sequence_id: int,
    lead_filters: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Enroll leads in sequence based on filters"""
    try:
        sequence = db.query(EmailSequence).filter(EmailSequence.id == sequence_id).first()
        if not sequence:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        # Start enrollment in background
        background_tasks.add_task(
            _enroll_leads_background,
            sequence_id,
            lead_filters,
            db
        )
        
        return {
            "message": f"Lead enrollment started for sequence {sequence_id}",
            "sequence_name": sequence.name,
            "filters": lead_filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _enroll_leads_background(sequence_id: int, lead_filters: Dict, db: Session):
    """Background task for lead enrollment"""
    try:
        manager = SequenceManager(db)
        enrolled_count = await manager.start_sequence_for_leads(sequence_id, lead_filters)
        logger.info(f"✅ Enrolled {enrolled_count} leads in sequence {sequence_id}")
    except Exception as e:
        logger.error(f"❌ Lead enrollment failed: {str(e)}")

@app.get("/sequences/{sequence_id}/performance")
async def get_sequence_performance(
    sequence_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get sequence performance metrics"""
    try:
        sequence = db.query(EmailSequence).filter(EmailSequence.id == sequence_id).first()
        if not sequence:
            raise HTTPException(status_code=404, detail="Sequence not found")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get enrollments
        enrollments = db.query(SequenceEnrollment).filter(
            and_(
                SequenceEnrollment.sequence_id == sequence_id,
                SequenceEnrollment.enrolled_at >= cutoff_date
            )
        ).all()
        
        # Get emails
        emails = db.query(Email).join(SequenceStep).filter(
            and_(
                SequenceStep.sequence_id == sequence_id,
                Email.created_at >= cutoff_date
            )
        ).all()
        
        # Calculate metrics
        total_enrollments = len(enrollments)
        total_emails = len(emails)
        total_sent = len([e for e in emails if e.status == EmailStatus.SENT])
        total_opened = len([e for e in emails if e.opened_at])
        total_clicked = len([e for e in emails if e.clicked_at])
        total_replied = len([e for e in emails if e.replied_at])
        
        metrics = {
            'sequence_id': sequence_id,
            'sequence_name': sequence.name,
            'period_days': days,
            'total_enrollments': total_enrollments,
            'total_emails': total_emails,
            'emails_sent': total_sent,
            'emails_opened': total_opened,
            'emails_clicked': total_clicked,
            'emails_replied': total_replied,
            'open_rate': (total_opened / total_sent * 100) if total_sent > 0 else 0,
            'click_rate': (total_clicked / total_sent * 100) if total_sent > 0 else 0,
            'reply_rate': (total_replied / total_sent * 100) if total_sent > 0 else 0,
            'completion_rate': len([e for e in enrollments if e.status == SequenceStatus.COMPLETED]) / total_enrollments * 100 if total_enrollments > 0 else 0
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Failed to get sequence performance: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# 🎬 LOOM VIDEO ENDPOINTS
# ============================================================================

@app.post("/loom-videos", response_model=LoomVideoResponse, status_code=201)
async def create_loom_video(
    video: LoomVideoCreate,
    db: Session = Depends(get_db)
):
    """Register new Loom video"""
    try:
        # Get video info from Loom API
        loom_service = LoomService()
        video_info = loom_service.get_video_info(video.loom_id)
        
        if not video_info:
            raise HTTPException(status_code=400, detail="Invalid Loom video ID")
        
        # Create video record
        db_video = LoomVideo(
            **video.dict(),
            duration=video_info.get('duration'),
            thumbnail_url=video_info.get('thumbnail_url'),
            embed_url=video_info.get('embed_url'),
            share_url=video_info.get('share_url')
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        logger.info(f"✅ Registered Loom video {db_video.id}: {video.loom_id}")
        
        return LoomVideoResponse.from_orm(db_video)
        
    except Exception as e:
        logger.error(f"❌ Failed to create Loom video: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/loom-videos", response_model=List[LoomVideoResponse])
async def get_loom_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    video_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get Loom videos"""
    try:
        query = db.query(LoomVideo).filter(LoomVideo.is_active == True)
        
        if video_type:
            query = query.filter(LoomVideo.video_type == video_type)
        
        videos = query.offset(skip).limit(limit).all()
        return [LoomVideoResponse.from_orm(v) for v in videos]
        
    except Exception as e:
        logger.error(f"❌ Failed to get Loom videos: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/loom-videos/{video_id}/custom-thumbnail")
async def generate_custom_thumbnail(
    video_id: int,
    lead_name: str = Body(...),
    custom_message: str = Body(""),
    db: Session = Depends(get_db)
):
    """Generate custom thumbnail for Loom video"""
    try:
        video = db.query(LoomVideo).filter(LoomVideo.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        loom_service = LoomService()
        thumbnail_url = loom_service.create_custom_thumbnail(
            video.loom_id,
            lead_name,
            custom_message
        )
        
        return {
            "video_id": video_id,
            "lead_name": lead_name,
            "custom_thumbnail_url": thumbnail_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# 📊 ANALYTICS & PERFORMANCE ENDPOINTS
# ============================================================================

@app.get("/analytics/overview")
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get email analytics overview"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all emails in period
        emails = db.query(Email).filter(Email.created_at >= cutoff_date).all()
        
        total_emails = len(emails)
        sent_emails = [e for e in emails if e.status == EmailStatus.SENT]
        
        metrics = {
            'period_days': days,
            'total_emails': total_emails,
            'emails_sent': len(sent_emails),
            'emails_delivered': len([e for e in emails if e.status == EmailStatus.DELIVERED]),
            'emails_opened': len([e for e in emails if e.opened_at]),
            'emails_clicked': len([e for e in emails if e.clicked_at]),
            'emails_replied': len([e for e in emails if e.replied_at]),
            'emails_bounced': len([e for e in emails if e.status == EmailStatus.BOUNCED]),
            'emails_spam': len([e for e in emails if e.status == EmailStatus.SPAM]),
            'loom_clicks': len([e for e in emails if e.loom_clicked]),
        }
        
        # Calculate rates
        if len(sent_emails) > 0:
            metrics.update({
                'delivery_rate': metrics['emails_delivered'] / metrics['emails_sent'] * 100,
                'open_rate': metrics['emails_opened'] / metrics['emails_sent'] * 100,
                'click_rate': metrics['emails_clicked'] / metrics['emails_sent'] * 100,
                'reply_rate': metrics['emails_replied'] / metrics['emails_sent'] * 100,
                'bounce_rate': metrics['emails_bounced'] / metrics['emails_sent'] * 100,
                'loom_click_rate': metrics['loom_clicks'] / metrics['emails_sent'] * 100
            })
        else:
            metrics.update({
                'delivery_rate': 0,
                'open_rate': 0,
                'click_rate': 0,
                'reply_rate': 0,
                'bounce_rate': 0,
                'loom_click_rate': 0
            })
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Failed to get analytics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analytics/templates")
async def get_template_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get per-template analytics"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get templates with email stats
        templates = db.query(EmailTemplate).all()
        template_stats = []
        
        for template in templates:
            emails = db.query(Email).filter(
                and_(
                    Email.template_id == template.id,
                    Email.created_at >= cutoff_date
                )
            ).all()
            
            sent_count = len([e for e in emails if e.status == EmailStatus.SENT])
            
            stats = {
                'template_id': template.id,
                'template_name': template.name,
                'emails_sent': sent_count,
                'open_rate': len([e for e in emails if e.opened_at]) / sent_count * 100 if sent_count > 0 else 0,
                'click_rate': len([e for e in emails if e.clicked_at]) / sent_count * 100 if sent_count > 0 else 0,
                'reply_rate': len([e for e in emails if e.replied_at]) / sent_count * 100 if sent_count > 0 else 0,
                'loom_click_rate': len([e for e in emails if e.loom_clicked]) / sent_count * 100 if sent_count > 0 else 0
            }
            
            template_stats.append(stats)
        
        # Sort by performance
        template_stats.sort(key=lambda x: x['reply_rate'], reverse=True)
        
        return template_stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get template analytics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# 🔄 AUTOMATION CONTROL ENDPOINTS
# ============================================================================

@app.post("/automation/trigger")
async def trigger_automation(
    trigger_data: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks
):
    """Manually trigger automation for leads"""
    try:
        lead_id = trigger_data.get('lead_id')
        trigger_type = trigger_data.get('trigger_type', 'manual')
        
        if not lead_id:
            raise HTTPException(status_code=400, detail="lead_id is required")
        
        # Trigger sequences in background
        background_tasks.add_task(
            _trigger_sequences_background,
            lead_id,
            trigger_type,
            trigger_data
        )
        
        return {
            "message": f"Automation triggered for lead {lead_id}",
            "trigger_type": trigger_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _trigger_sequences_background(lead_id: int, trigger_type: str, trigger_data: Dict):
    """Background task for triggering sequences"""
    try:
        result = trigger_sequence_for_lead.delay(lead_id, trigger_type, trigger_data)
        logger.info(f"✅ Triggered sequences for lead {lead_id}: {result}")
    except Exception as e:
        logger.error(f"❌ Trigger failed for lead {lead_id}: {str(e)}")

@app.post("/automation/process")
async def manual_process_sequences(background_tasks: BackgroundTasks):
    """Manually trigger sequence processing"""
    try:
        background_tasks.add_task(_process_sequences_background)
        
        return {"message": "Sequence processing started"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _process_sequences_background():
    """Background task for processing sequences"""
    try:
        result = process_sequences.delay()
        logger.info(f"✅ Processing sequences: {result}")
    except Exception as e:
        logger.error(f"❌ Sequence processing failed: {str(e)}")

# ============================================================================
# 🚀 HEALTH CHECK & INFO ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Email Engine",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Mass personalization",
            "Loom integration",
            "Sequence automation",
            "Performance analytics"
        ]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "📧 Hunter Agency - Email Engine API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "🎨 Template Engine with Jinja2",
            "🎬 Loom Video Integration",
            "⚡ Sequence Automation",
            "📊 Real-time Analytics",
            "🚀 Mass Personalization"
        ],
        "endpoints": {
            "templates": "/templates",
            "sequences": "/sequences", 
            "loom_videos": "/loom-videos",
            "analytics": "/analytics/overview",
            "automation": "/automation/trigger"
        }
    }

# ============================================================================
# 🎯 EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("📧 Starting Hunter Agency Email Engine API...")
    print("🎯 Features:")
    print("  ✅ Template Management with Loom Integration")
    print("  ✅ Sequence Automation & Enrollment")
    print("  ✅ Mass Personalization Engine")
    print("  ✅ Real-time Performance Analytics")
    print("  ✅ Background Task Processing")
    print("\n🚀 API Documentation: http://localhost:8001/docs")
    
    uvicorn.run(
        "email_engine_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
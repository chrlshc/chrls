#!/usr/bin/env python3
"""
📧 HUNTER AGENCY - Email Engine Models
Advanced email automation with Loom integration & personalization
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field, HttpUrl
import re

Base = declarative_base()

# ============================================================================
# 🏷️ ENUMS & CONSTANTS
# ============================================================================

class CampaignType(str, Enum):
    COLD_OUTREACH = "cold_outreach"
    WELCOME = "welcome"
    NURTURING = "nurturing"
    FOLLOW_UP = "follow_up"
    UPSELL = "upsell"
    WIN_BACK = "win_back"
    ABANDONED_CART = "abandoned_cart"

class EmailStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    SPAM = "spam"
    UNSUBSCRIBED = "unsubscribed"

class SequenceStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"

class TriggerType(str, Enum):
    LEAD_QUALIFIED = "lead_qualified"
    LEAD_GRADE_CHANGE = "lead_grade_change"
    NO_RESPONSE = "no_response"
    MANUAL = "manual"
    TIME_BASED = "time_based"
    BEHAVIOR = "behavior"

class LoomType(str, Enum):
    INTRO = "intro"               # Introduction personnalisée
    DEMO = "demo"                # Démonstration produit
    PROPOSAL = "proposal"        # Présentation d'offre
    FOLLOW_UP = "follow_up"      # Relance
    TESTIMONIAL = "testimonial"  # Témoignage client
    CASE_STUDY = "case_study"    # Étude de cas

# ============================================================================
# 📧 EMAIL TEMPLATE MODELS
# ============================================================================

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True)
    
    # Template Content
    subject_template = Column(String(500), nullable=False)
    html_template = Column(Text, nullable=False)
    text_template = Column(Text)
    
    # Personalization
    merge_tags = Column(JSON, default=[])  # Available tags: [first_name, company, etc.]
    dynamic_content = Column(JSON, default={})  # Conditional content blocks
    
    # Loom Integration
    loom_video_id = Column(String(255))
    loom_type = Column(String(50))  # LoomType
    loom_thumbnail_url = Column(String(500))
    loom_duration = Column(Integer)  # seconds
    
    # Configuration
    category = Column(String(100))
    tags = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    
    # Performance
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    reply_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    
    # Metadata
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sequence_steps = relationship("SequenceStep", back_populates="template")
    emails = relationship("Email", back_populates="template")

class EmailSequence(Base):
    __tablename__ = "email_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True)
    
    # Configuration
    campaign_type = Column(String(50), nullable=False)  # CampaignType
    description = Column(Text)
    
    # Targeting
    target_grades = Column(JSON, default=[])  # Lead grades to target
    target_sources = Column(JSON, default=[])  # Lead sources
    target_industries = Column(JSON, default=[])
    
    # Behavior
    trigger_type = Column(String(50), nullable=False)  # TriggerType
    trigger_conditions = Column(JSON, default={})
    
    # Settings
    is_active = Column(Boolean, default=True)
    max_emails_per_day = Column(Integer, default=50)
    time_zone = Column(String(50), default="UTC")
    sending_schedule = Column(JSON, default={})  # Days/hours to send
    
    # Performance Tracking
    total_sent = Column(Integer, default=0)
    total_opens = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    steps = relationship("SequenceStep", back_populates="sequence", order_by="SequenceStep.step_number")
    enrollments = relationship("SequenceEnrollment", back_populates="sequence")

class SequenceStep(Base):
    __tablename__ = "sequence_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, ForeignKey("email_sequences.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=False)
    
    # Step Configuration
    step_number = Column(Integer, nullable=False)
    name = Column(String(255))
    
    # Timing
    delay_days = Column(Integer, default=0)
    delay_hours = Column(Integer, default=0)
    delay_minutes = Column(Integer, default=0)
    
    # Conditions
    send_conditions = Column(JSON, default={})  # Conditions to send this step
    skip_conditions = Column(JSON, default={})  # Conditions to skip this step
    
    # Behavior
    stop_on_reply = Column(Boolean, default=True)
    stop_on_click = Column(Boolean, default=False)
    
    # A/B Testing
    ab_test_variant = Column(String(10))  # A, B, C, etc.
    ab_test_weight = Column(Float, default=100.0)  # Percentage
    
    # Performance
    sent_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sequence = relationship("EmailSequence", back_populates="steps")
    template = relationship("EmailTemplate", back_populates="sequence_steps")
    emails = relationship("Email", back_populates="sequence_step")

# ============================================================================
# 📨 EMAIL CAMPAIGN MODELS
# ============================================================================

class EmailCampaign(Base):
    __tablename__ = "email_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Campaign Details
    campaign_type = Column(String(50), nullable=False)
    subject = Column(String(500), nullable=False)
    
    # Content
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    
    # Targeting
    target_list_ids = Column(JSON, default=[])
    target_filters = Column(JSON, default={})
    
    # Loom Integration
    loom_video_id = Column(String(255))
    loom_thumbnail_url = Column(String(500))
    loom_click_tracking = Column(Boolean, default=True)
    
    # Scheduling
    send_at = Column(DateTime)
    time_zone = Column(String(50), default="UTC")
    
    # Status
    status = Column(String(50), default="draft")
    is_sent = Column(Boolean, default=False)
    
    # Performance
    recipients_count = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    unsubscribed_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Relationships
    emails = relationship("Email", back_populates="campaign")

class SequenceEnrollment(Base):
    __tablename__ = "sequence_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, ForeignKey("email_sequences.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    
    # Enrollment Details
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    enrolled_by = Column(String(255))
    
    # Status
    status = Column(String(50), default=SequenceStatus.ACTIVE)
    current_step = Column(Integer, default=1)
    
    # Progress
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    
    # Completion
    completed_at = Column(DateTime)
    stopped_at = Column(DateTime)
    stop_reason = Column(String(255))
    
    # Next Action
    next_email_at = Column(DateTime)
    
    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sequence = relationship("EmailSequence", back_populates="enrollments")
    # lead = relationship("Lead", back_populates="sequence_enrollments")

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    template_id = Column(Integer, ForeignKey("email_templates.id"))
    campaign_id = Column(Integer, ForeignKey("email_campaigns.id"))
    sequence_step_id = Column(Integer, ForeignKey("sequence_steps.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("sequence_enrollments.id"))
    
    # Email Details
    to_email = Column(String(255), nullable=False)
    to_name = Column(String(255))
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255))
    
    # Content (rendered)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    
    # Personalization Data
    merge_data = Column(JSON, default={})
    
    # Loom Tracking
    loom_video_id = Column(String(255))
    loom_clicked = Column(Boolean, default=False)
    loom_clicked_at = Column(DateTime)
    loom_view_duration = Column(Integer)  # seconds
    
    # Status & Delivery
    status = Column(String(50), default=EmailStatus.DRAFT)
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Engagement
    opened_at = Column(DateTime)
    first_opened_at = Column(DateTime)
    open_count = Column(Integer, default=0)
    
    clicked_at = Column(DateTime)
    first_clicked_at = Column(DateTime)
    click_count = Column(Integer, default=0)
    
    replied_at = Column(DateTime)
    reply_content = Column(Text)
    
    # Delivery Issues
    bounced_at = Column(DateTime)
    bounce_reason = Column(String(500))
    spam_at = Column(DateTime)
    unsubscribed_at = Column(DateTime)
    
    # Provider Data
    provider_message_id = Column(String(255))  # SendGrid, Mailgun, etc.
    provider_response = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = relationship("EmailTemplate", back_populates="emails")
    campaign = relationship("EmailCampaign", back_populates="emails")
    sequence_step = relationship("SequenceStep", back_populates="emails")
    # lead = relationship("Lead", back_populates="emails")

# ============================================================================
# 🎬 LOOM INTEGRATION MODELS
# ============================================================================

class LoomVideo(Base):
    __tablename__ = "loom_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Loom Details
    loom_id = Column(String(255), unique=True, nullable=False)
    title = Column(String(500))
    description = Column(Text)
    
    # Video Properties
    duration = Column(Integer)  # seconds
    thumbnail_url = Column(String(500))
    embed_url = Column(String(500))
    share_url = Column(String(500))
    
    # Categorization
    video_type = Column(String(50))  # LoomType
    tags = Column(JSON, default=[])
    target_audience = Column(JSON, default=[])  # Lead grades, industries, etc.
    
    # Performance
    total_views = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    average_view_duration = Column(Float, default=0.0)
    
    # Usage
    times_used = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Metadata
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class LoomClick(Base):
    __tablename__ = "loom_clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    loom_video_id = Column(String(255), nullable=False)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    
    # Click Details
    clicked_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Viewing Data
    view_duration = Column(Integer)  # seconds watched
    completion_rate = Column(Float)  # percentage watched
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# 🔄 PYDANTIC SCHEMAS
# ============================================================================

class EmailTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    subject_template: str = Field(..., min_length=1, max_length=500)
    html_template: str
    text_template: Optional[str] = None
    merge_tags: List[str] = []
    loom_video_id: Optional[str] = None
    loom_type: Optional[LoomType] = None
    category: Optional[str] = None
    tags: List[str] = []

class EmailTemplateCreate(EmailTemplateBase):
    slug: Optional[str] = None

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject_template: Optional[str] = None
    html_template: Optional[str] = None
    text_template: Optional[str] = None
    loom_video_id: Optional[str] = None
    is_active: Optional[bool] = None

class EmailTemplateResponse(EmailTemplateBase):
    id: int
    slug: str
    loom_thumbnail_url: Optional[str]
    open_rate: float
    click_rate: float
    reply_rate: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmailSequenceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    campaign_type: CampaignType
    description: Optional[str] = None
    target_grades: List[str] = []
    target_sources: List[str] = []
    trigger_type: TriggerType
    max_emails_per_day: int = Field(50, ge=1, le=1000)

class EmailSequenceCreate(EmailSequenceBase):
    slug: Optional[str] = None

class EmailSequenceResponse(EmailSequenceBase):
    id: int
    slug: str
    is_active: bool
    total_sent: int
    total_opens: int
    total_clicks: int
    total_replies: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoomVideoBase(BaseModel):
    loom_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    video_type: LoomType
    tags: List[str] = []

class LoomVideoCreate(LoomVideoBase):
    pass

class LoomVideoResponse(LoomVideoBase):
    id: int
    duration: Optional[int]
    thumbnail_url: Optional[str]
    embed_url: Optional[str]
    total_views: int
    total_clicks: int
    times_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmailMetrics(BaseModel):
    total_sent: int
    delivered_rate: float
    open_rate: float
    click_rate: float
    reply_rate: float
    conversion_rate: float
    loom_click_rate: float
    unsubscribe_rate: float
    bounce_rate: float

class CampaignPerformance(BaseModel):
    campaign_id: int
    campaign_name: str
    metrics: EmailMetrics
    revenue_generated: float
    cost_per_conversion: float
    roi: float

# ============================================================================
# 🎯 MERGE TAG PROCESSOR
# ============================================================================

class MergeTagProcessor:
    """Process merge tags in email templates"""
    
    AVAILABLE_TAGS = {
        # Lead Info
        'first_name': 'Lead first name',
        'last_name': 'Lead last name', 
        'full_name': 'Lead full name',
        'email': 'Lead email',
        'phone': 'Lead phone',
        'company': 'Lead company',
        'industry': 'Lead industry',
        'location': 'Lead location',
        'budget': 'Lead budget estimate',
        'source': 'Lead source',
        'grade': 'Lead grade (hot/warm/cold)',
        
        # Social Media
        'instagram_handle': 'Instagram handle',
        'linkedin_profile': 'LinkedIn profile',
        'twitter_handle': 'Twitter handle',
        
        # Personalization
        'niche': 'Lead niche/specialization',
        'pain_point': 'Identified pain point',
        'goal': 'Lead goal/objective',
        'timeline': 'Project timeline',
        
        # Dynamic
        'current_date': 'Current date',
        'day_of_week': 'Day of the week',
        'sender_name': 'Sender name',
        'sender_company': 'Sender company'
    }
    
    @staticmethod
    def extract_tags(template: str) -> List[str]:
        """Extract all merge tags from template"""
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        return re.findall(pattern, template)
    
    @staticmethod
    def validate_tags(template: str) -> Dict[str, bool]:
        """Validate all tags in template"""
        tags = MergeTagProcessor.extract_tags(template)
        return {
            tag: tag in MergeTagProcessor.AVAILABLE_TAGS 
            for tag in tags
        }
    
    @staticmethod
    def get_tag_description(tag: str) -> str:
        """Get description for a tag"""
        return MergeTagProcessor.AVAILABLE_TAGS.get(tag, "Unknown tag")

# ============================================================================
# 🎯 EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example email template with merge tags
    template_html = """
    <h1>Hey {{first_name}}! 👋</h1>
    
    <p>I saw your {{source}} profile and noticed you're in {{industry}}. 
    As someone working in {{location}}, you might be interested in this...</p>
    
    <!-- Loom Video Integration -->
    <div style="text-align: center; margin: 20px 0;">
        <a href="{{loom_url}}" target="_blank">
            <img src="{{loom_thumbnail}}" 
                 alt="Personal video for {{first_name}}" 
                 style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <div style="margin-top: 10px; color: #007bff;">
                ▶️ Watch my personal message for you ({{loom_duration}}s)
            </div>
        </a>
    </div>
    
    <p>Based on your {{grade}} lead score, I think we could help you achieve {{goal}}.</p>
    
    <p>Best regards,<br>{{sender_name}}</p>
    """
    
    # Extract and validate tags
    tags = MergeTagProcessor.extract_tags(template_html)
    validation = MergeTagProcessor.validate_tags(template_html)
    
    print("📧 Email Template Analysis")
    print("=" * 40)
    print(f"Found tags: {tags}")
    print(f"Validation: {validation}")
    
    # Example merge data
    merge_data = {
        'first_name': 'Sophie',
        'source': 'Instagram',
        'industry': 'Fashion',
        'location': 'Paris',
        'grade': 'hot',
        'goal': 'premium photography',
        'sender_name': 'Alex Hunter',
        'loom_url': 'https://loom.com/share/abc123',
        'loom_thumbnail': 'https://cdn.loom.com/sessions/thumbnails/abc123.jpg',
        'loom_duration': '45'
    }
    
    print(f"\n🎯 Sample merge data: {merge_data}")
    print("\n🚀 Email Engine Models Ready!")
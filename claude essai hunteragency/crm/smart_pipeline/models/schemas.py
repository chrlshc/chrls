"""
=Ê CRM SMART PIPELINE - SCHEMAS
Modules de données pour le pipeline CRM
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURING = "nurturing"

class OpportunityStage(str, Enum):
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class LeadSource(str, Enum):
    MANUAL = "manual"
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    REFERRAL = "referral"
    EMAIL_CAMPAIGN = "email_campaign"
    SOCIAL_MEDIA = "social_media"
    COLD_OUTREACH = "cold_outreach"
    WEBINAR = "webinar"
    TRADE_SHOW = "trade_show"

class Lead(BaseModel):
    id: Optional[int] = None
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source: LeadSource = LeadSource.MANUAL
    industry: Optional[str] = None
    budget_range: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    score: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Email invalide')
        return v.lower()
    
    @validator('score')
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Le score doit être entre 0 et 10')
        return v

class LeadCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source: LeadSource = LeadSource.MANUAL
    industry: Optional[str] = None
    budget_range: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []

class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    budget_range: Optional[str] = None
    status: Optional[LeadStatus] = None
    score: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    next_follow_up: Optional[datetime] = None

class Opportunity(BaseModel):
    id: Optional[int] = None
    lead_id: int
    title: str
    description: Optional[str] = None
    value: float
    stage: OpportunityStage = OpportunityStage.QUALIFICATION
    probability: float = 0.25
    close_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('La valeur doit être positive')
        return v
    
    @validator('probability')
    def validate_probability(cls, v):
        if v < 0 or v > 1:
            raise ValueError('La probabilité doit être entre 0 et 1')
        return v

class OpportunityCreate(BaseModel):
    lead_id: int
    title: str
    description: Optional[str] = None
    value: float
    stage: OpportunityStage = OpportunityStage.QUALIFICATION
    probability: float = 0.25
    close_date: Optional[datetime] = None

class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[OpportunityStage] = None
    probability: Optional[float] = None
    close_date: Optional[datetime] = None

class Activity(BaseModel):
    id: Optional[int] = None
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    type: str  # call, email, meeting, note, etc.
    subject: str
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

class ActivityCreate(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    type: str
    subject: str
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class PipelineMetrics(BaseModel):
    total_leads: int
    total_opportunities: int
    total_pipeline_value: float
    conversion_rate: float
    avg_deal_size: float
    leads_by_status: Dict[str, int]
    opportunities_by_stage: Dict[str, Dict[str, Any]]
    monthly_trend: List[Dict[str, Any]]

class LeadScoreBreakdown(BaseModel):
    total_score: float
    contact_quality: float
    engagement_level: float
    fit_score: float
    behavioral_score: float
    demographic_score: float
    scoring_factors: List[Dict[str, Any]]

class QualificationCriteria(BaseModel):
    budget_confirmed: bool = False
    authority_confirmed: bool = False
    need_confirmed: bool = False
    timeline_confirmed: bool = False
    fit_score: float = 0.0
    qualification_notes: Optional[str] = None

class LeadEnrichmentData(BaseModel):
    social_profiles: Optional[Dict[str, str]] = {}
    company_info: Optional[Dict[str, Any]] = {}
    technology_stack: Optional[List[str]] = []
    industry_insights: Optional[Dict[str, Any]] = {}
    contact_verified: bool = False
    enrichment_date: Optional[datetime] = None

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from . import LeadStatus, LeadGrade


class LeadBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    status: LeadStatus = LeadStatus.NEW
    stage_id: Optional[int] = Field(default=None, ge=1)


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[LeadStatus] = None
    stage_id: Optional[int] = None
    grade: Optional[LeadGrade] = None
    ai_score: Optional[float] = None


class LeadRead(LeadBase):
    id: int
    grade: Optional[LeadGrade] = None
    ai_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipelineStageBase(BaseModel):
    name: str
    order: int
    pipeline_id: Optional[int] = None


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageRead(PipelineStageBase):
    id: int

    class Config:
        from_attributes = True

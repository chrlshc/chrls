from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    WON = "won"
    LOST = "lost"


class LeadGrade(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    stages = relationship("PipelineStage", back_populates="pipeline")


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    pipeline = relationship("Pipeline", back_populates="stages")
    leads = relationship("Lead", back_populates="stage")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    status = Column(SAEnum(LeadStatus), default=LeadStatus.NEW)
    grade = Column(SAEnum(LeadGrade), nullable=True)
    ai_score = Column(Float, nullable=True)
    stage_id = Column(Integer, ForeignKey("pipeline_stages.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stage = relationship("PipelineStage", back_populates="leads")

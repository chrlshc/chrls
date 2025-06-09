from sqlalchemy.orm import Session

from ..models import Lead, PipelineStage
from ..models.schemas import (
    LeadCreate,
    LeadUpdate,
    PipelineStageCreate,
)


class LeadService:
    def __init__(self, db: Session):
        self.db = db

    def create_lead(self, data: LeadCreate) -> Lead:
        lead = Lead(**data.dict())
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def get_lead(self, lead_id: int) -> Lead | None:
        return self.db.query(Lead).filter(Lead.id == lead_id).first()

    def list_leads(self):
        return self.db.query(Lead).all()

    def update_lead(self, lead_id: int, data: LeadUpdate) -> Lead | None:
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        for field, value in data.dict(exclude_unset=True).items():
            setattr(lead, field, value)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def delete_lead(self, lead_id: int) -> bool:
        lead = self.get_lead(lead_id)
        if not lead:
            return False
        self.db.delete(lead)
        self.db.commit()
        return True


class PipelineStageService:
    def __init__(self, db: Session):
        self.db = db

    def create_stage(self, data: PipelineStageCreate) -> PipelineStage:
        stage = PipelineStage(**data.dict())
        self.db.add(stage)
        self.db.commit()
        self.db.refresh(stage)
        return stage

    def list_stages(self):
        return self.db.query(PipelineStage).all()

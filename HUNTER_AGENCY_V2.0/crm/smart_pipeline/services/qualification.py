from sqlalchemy.orm import Session

from ..models import Lead, LeadGrade


class LeadQualificationService:
    def __init__(self, db: Session):
        self.db = db

    def qualify(self, lead_id: int) -> Lead:
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")
        # naive scoring based on name length
        lead.ai_score = min(len(lead.name) * 10, 100)
        if lead.ai_score >= 70:
            lead.grade = LeadGrade.HOT
        elif lead.ai_score >= 40:
            lead.grade = LeadGrade.WARM
        else:
            lead.grade = LeadGrade.COLD
        self.db.commit()
        self.db.refresh(lead)
        return lead

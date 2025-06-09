from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..models import Base, Lead, PipelineStage
from ..models.schemas import (
    LeadCreate,
    LeadRead,
    LeadUpdate,
    PipelineStageCreate,
    PipelineStageRead,
)
from ..services import LeadService, PipelineStageService

DATABASE_URL = "sqlite:///./smart_pipeline.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Pipeline")
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {"status": "ok"}


# Lead endpoints
@router.post("/leads", response_model=LeadRead, status_code=201)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    service = LeadService(db)
    return service.create_lead(lead)


@router.get("/leads", response_model=list[LeadRead])
def list_leads(db: Session = Depends(get_db)):
    service = LeadService(db)
    return service.list_leads()


@router.get("/leads/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    service = LeadService(db)
    lead = service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/leads/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    service = LeadService(db)
    lead = service.update_lead(lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    service = LeadService(db)
    if not service.delete_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True}


# Pipeline stage endpoints
@router.post("/stages", response_model=PipelineStageRead, status_code=201)
def create_stage(stage: PipelineStageCreate, db: Session = Depends(get_db)):
    service = PipelineStageService(db)
    return service.create_stage(stage)


@router.get("/stages", response_model=list[PipelineStageRead])
def list_stages(db: Session = Depends(get_db)):
    service = PipelineStageService(db)
    return service.list_stages()


app.include_router(router)

"""
=� CRM SMART PIPELINE - API ROUTES
Gestion des leads et des opportunit�s commerciales
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
import aiosqlite

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

class LeadCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source: str = "manual"
    industry: Optional[str] = None
    budget_range: Optional[str] = None
    notes: Optional[str] = None

class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    budget_range: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class OpportunityCreate(BaseModel):
    lead_id: int
    title: str
    value: float
    stage: str = "qualification"
    close_date: Optional[datetime] = None
    probability: float = 0.25
    description: Optional[str] = None

@router.post("/leads", response_model=dict)
async def create_lead(lead: LeadCreate):
    """Cr�er un nouveau lead"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            cursor = await db.execute("""
                INSERT INTO pipeline_leads 
                (email, first_name, last_name, company, phone, source, industry, budget_range, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
            """, (
                lead.email, lead.first_name, lead.last_name,
                lead.company, lead.phone, lead.source,
                lead.industry, lead.budget_range, lead.notes,
                datetime.now()
            ))
            
            lead_id = cursor.lastrowid
            await db.commit()
            
            return {
                "id": lead_id,
                "message": "Lead cr�� avec succ�s",
                "email": lead.email,
                "status": "new"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur cr�ation lead: {str(e)}")

@router.get("/leads", response_model=List[dict])
async def get_leads(status: Optional[str] = None, limit: int = 50):
    """R�cup�rer la liste des leads"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            if status:
                query = "SELECT * FROM pipeline_leads WHERE status = ? ORDER BY created_at DESC LIMIT ?"
                cursor = await db.execute(query, (status, limit))
            else:
                query = "SELECT * FROM pipeline_leads ORDER BY created_at DESC LIMIT ?"
                cursor = await db.execute(query, (limit,))
            
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            leads = [dict(zip(columns, row)) for row in rows]
            return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur r�cup�ration leads: {str(e)}")

@router.get("/leads/{lead_id}", response_model=dict)
async def get_lead(lead_id: int):
    """R�cup�rer un lead sp�cifique"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            cursor = await db.execute("SELECT * FROM pipeline_leads WHERE id = ?", (lead_id,))
            row = await cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Lead non trouv�")
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur r�cup�ration lead: {str(e)}")

@router.put("/leads/{lead_id}", response_model=dict)
async def update_lead(lead_id: int, lead_update: LeadUpdate):
    """Mettre � jour un lead"""
    try:
        update_fields = []
        values = []
        
        for field, value in lead_update.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="Aucun champ � mettre � jour")
        
        values.append(datetime.now())
        values.append(lead_id)
        
        query = f"UPDATE pipeline_leads SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?"
        
        async with aiosqlite.connect("hunter_agency.db") as db:
            await db.execute(query, values)
            await db.commit()
            
            return {"message": "Lead mis � jour avec succ�s", "id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur mise � jour lead: {str(e)}")

@router.post("/opportunities", response_model=dict)
async def create_opportunity(opportunity: OpportunityCreate):
    """Cr�er une nouvelle opportunit�"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            cursor = await db.execute("""
                INSERT INTO pipeline_opportunities 
                (lead_id, title, value, stage, close_date, probability, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity.lead_id, opportunity.title, opportunity.value,
                opportunity.stage, opportunity.close_date, opportunity.probability,
                opportunity.description, datetime.now()
            ))
            
            opp_id = cursor.lastrowid
            await db.commit()
            
            return {
                "id": opp_id,
                "message": "Opportunit� cr��e avec succ�s",
                "value": opportunity.value,
                "stage": opportunity.stage
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur cr�ation opportunit�: {str(e)}")

@router.get("/analytics", response_model=dict)
async def get_pipeline_analytics():
    """R�cup�rer les analytics du pipeline"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            # Leads par statut
            cursor = await db.execute("""
                SELECT status, COUNT(*) as count 
                FROM pipeline_leads 
                GROUP BY status
            """)
            status_counts = dict(await cursor.fetchall())
            
            # Opportunit�s par �tape
            cursor = await db.execute("""
                SELECT stage, COUNT(*) as count, SUM(value) as total_value
                FROM pipeline_opportunities 
                GROUP BY stage
            """)
            stage_data = await cursor.fetchall()
            
            # Conversion rates
            cursor = await db.execute("""
                SELECT 
                    COUNT(DISTINCT pl.id) as total_leads,
                    COUNT(DISTINCT po.id) as total_opportunities
                FROM pipeline_leads pl
                LEFT JOIN pipeline_opportunities po ON pl.id = po.lead_id
            """)
            conversion_data = await cursor.fetchone()
            
            return {
                "leads_by_status": status_counts,
                "opportunities_by_stage": [
                    {"stage": row[0], "count": row[1], "value": row[2] or 0}
                    for row in stage_data
                ],
                "conversion_rate": (
                    conversion_data[1] / conversion_data[0] * 100 
                    if conversion_data[0] > 0 else 0
                )
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics: {str(e)}")

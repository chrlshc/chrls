"""
🚀 Hunter Agency V2.2 - Advanced Dashboard Backend
Intégration avec les vraies données CRM et email automation
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import aiosqlite
from databases import Database

# Ajouter le répertoire parent au path pour les imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

app = FastAPI(
    title="Hunter Agency V2.2 - Dashboard API", 
    version="2.2.0",
    description="Advanced CRM and Email Automation Dashboard"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DATABASE_URL = "sqlite+aiosqlite:///./hunter_agency.db"
database = Database(DATABASE_URL)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class DashboardService:
    """Service pour récupérer les données du dashboard"""
    
    async def get_overview_stats(self) -> Dict[str, Any]:
        """Statistiques générales du dashboard"""
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                # Total leads
                cursor = await db.execute("SELECT COUNT(*) FROM leads")
                total_leads = (await cursor.fetchone())[0] or 0
                
                # Total CRM leads
                cursor = await db.execute("SELECT COUNT(*) FROM pipeline_leads")
                total_crm_leads = (await cursor.fetchone())[0] or 0
                
                # Emails sent this month
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM email_campaigns 
                    WHERE sent_at >= date('now', 'start of month')
                """)
                emails_this_month = (await cursor.fetchone())[0] or 0
                
                # Active sequences
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM lead_sequences WHERE status = 'active'
                """)
                active_sequences = (await cursor.fetchone())[0] or 0
                
                # Revenue projection (based on opportunities)
                cursor = await db.execute("""
                    SELECT SUM(value * probability) FROM pipeline_opportunities 
                    WHERE stage NOT IN ('closed_lost', 'closed_won')
                """)
                result = await cursor.fetchone()
                projected_revenue = result[0] if result[0] else 0
                
                # Conversion rates
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_emails,
                        COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opens,
                        COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicks
                    FROM email_campaigns 
                    WHERE sent_at >= date('now', '-30 days')
                """)
                email_data = await cursor.fetchone()
                
                total_emails = email_data[0] if email_data[0] else 1
                open_rate = (email_data[1] / total_emails * 100) if total_emails > 0 else 0
                click_rate = (email_data[2] / total_emails * 100) if total_emails > 0 else 0
                
                return {
                    "total_leads": total_leads + total_crm_leads,
                    "emails_sent": emails_this_month,
                    "active_sequences": active_sequences,
                    "projected_revenue": round(projected_revenue, 2),
                    "open_rate": round(open_rate, 1),
                    "click_rate": round(click_rate, 1),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error getting overview stats: {e}")
            return self._get_demo_stats()
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Activités récentes"""
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                # Recent leads
                cursor = await db.execute("""
                    SELECT 'lead_created' as type, first_name, email, created_at 
                    FROM leads 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit//2,))
                recent_leads = await cursor.fetchall()
                
                # Recent emails
                cursor = await db.execute("""
                    SELECT 'email_sent' as type, l.first_name, l.email, ec.sent_at as created_at
                    FROM email_campaigns ec
                    JOIN leads l ON ec.lead_id = l.id
                    ORDER BY ec.sent_at DESC 
                    LIMIT ?
                """, (limit//2,))
                recent_emails = await cursor.fetchall()
                
                # Combine and format
                activities = []
                for row in recent_leads + recent_emails:
                    activities.append({
                        "type": row[0],
                        "description": f"{row[1]} ({row[2]})",
                        "timestamp": row[3]
                    })
                
                # Sort by timestamp
                activities.sort(key=lambda x: x['timestamp'], reverse=True)
                return activities[:limit]
                
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    async def get_performance_charts(self) -> Dict[str, Any]:
        """Données pour les graphiques de performance"""
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                # Daily email stats for last 7 days
                daily_stats = []
                for i in range(7, 0, -1):
                    date = datetime.now() - timedelta(days=i)
                    date_str = date.strftime('%Y-%m-%d')
                    
                    cursor = await db.execute("""
                        SELECT COUNT(*) FROM email_campaigns 
                        WHERE date(sent_at) = ?
                    """, (date_str,))
                    count = (await cursor.fetchone())[0] or 0
                    
                    daily_stats.append({
                        "date": date_str,
                        "emails_sent": count,
                        "day": date.strftime('%a')
                    })
                
                # Lead sources
                cursor = await db.execute("""
                    SELECT source, COUNT(*) as count 
                    FROM leads 
                    GROUP BY source 
                    ORDER BY count DESC
                """)
                lead_sources = [{"source": row[0], "count": row[1]} for row in await cursor.fetchall()]
                
                # Email status distribution
                cursor = await db.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM email_campaigns 
                    WHERE sent_at >= date('now', '-30 days')
                    GROUP BY status
                """)
                email_status = [{"status": row[0], "count": row[1]} for row in await cursor.fetchall()]
                
                return {
                    "daily_email_stats": daily_stats,
                    "lead_sources": lead_sources,
                    "email_status": email_status
                }
        except Exception as e:
            print(f"Error getting performance charts: {e}")
            return {"daily_email_stats": [], "lead_sources": [], "email_status": []}
    
    async def get_lead_funnel(self) -> Dict[str, Any]:
        """Données du funnel de conversion"""
        try:
            async with aiosqlite.connect("hunter_agency.db") as db:
                # Lead statuses
                cursor = await db.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM pipeline_leads 
                    GROUP BY status 
                    ORDER BY 
                        CASE status 
                            WHEN 'new' THEN 1
                            WHEN 'contacted' THEN 2
                            WHEN 'qualified' THEN 3
                            WHEN 'proposal' THEN 4
                            WHEN 'negotiation' THEN 5
                            WHEN 'closed_won' THEN 6
                            WHEN 'closed_lost' THEN 7
                            ELSE 8
                        END
                """)
                funnel_data = [{"stage": row[0], "count": row[1]} for row in await cursor.fetchall()]
                
                # Opportunity stages
                cursor = await db.execute("""
                    SELECT stage, COUNT(*) as count, SUM(value) as total_value
                    FROM pipeline_opportunities 
                    GROUP BY stage
                """)
                opportunity_data = [
                    {"stage": row[0], "count": row[1], "value": row[2] or 0} 
                    for row in await cursor.fetchall()
                ]
                
                return {
                    "lead_funnel": funnel_data,
                    "opportunity_pipeline": opportunity_data
                }
        except Exception as e:
            print(f"Error getting lead funnel: {e}")
            return {"lead_funnel": [], "opportunity_pipeline": []}
    
    def _get_demo_stats(self) -> Dict[str, Any]:
        """Données de démonstration"""
        return {
            "total_leads": 1247,
            "emails_sent": 5832,
            "active_sequences": 23,
            "projected_revenue": 89750.00,
            "open_rate": 24.5,
            "click_rate": 4.7,
            "timestamp": datetime.now().isoformat()
        }

dashboard_service = DashboardService()

# Routes API
@app.get("/")
async def root():
    """Serve dashboard HTML"""
    return FileResponse("index.html")

@app.get("/api/overview")
async def get_overview():
    """Statistiques générales du dashboard"""
    stats = await dashboard_service.get_overview_stats()
    return JSONResponse(content=stats)

@app.get("/api/activity")
async def get_recent_activity(limit: int = 10):
    """Activités récentes"""
    activities = await dashboard_service.get_recent_activity(limit)
    return JSONResponse(content={"activities": activities})

@app.get("/api/charts")
async def get_charts():
    """Données pour les graphiques"""
    charts = await dashboard_service.get_performance_charts()
    return JSONResponse(content=charts)

@app.get("/api/funnel")
async def get_funnel():
    """Données du funnel de conversion"""
    funnel = await dashboard_service.get_lead_funnel()
    return JSONResponse(content=funnel)

@app.get("/api/leads/summary")
async def get_leads_summary():
    """Résumé des leads"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            # Total leads by source
            cursor = await db.execute("""
                SELECT source, COUNT(*) as count, AVG(grade) as avg_score
                FROM leads 
                GROUP BY source
                ORDER BY count DESC
            """)
            lead_sources = []
            for row in await cursor.fetchall():
                lead_sources.append({
                    "source": row[0],
                    "count": row[1],
                    "avg_score": round(row[2] or 0, 1)
                })
            
            return JSONResponse(content={"lead_sources": lead_sources})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/sequences/performance")
async def get_sequences_performance():
    """Performance des séquences email"""
    try:
        async with aiosqlite.connect("hunter_agency.db") as db:
            cursor = await db.execute("""
                SELECT 
                    es.name,
                    COUNT(DISTINCT ls.id) as total_leads,
                    COUNT(DISTINCT CASE WHEN ls.status = 'completed' THEN ls.id END) as completed,
                    COUNT(DISTINCT ec.id) as emails_sent,
                    COUNT(DISTINCT CASE WHEN ec.opened_at IS NOT NULL THEN ec.id END) as emails_opened
                FROM email_sequences es
                LEFT JOIN lead_sequences ls ON es.id = ls.sequence_id  
                LEFT JOIN email_campaigns ec ON ls.sequence_id = ec.sequence_id
                WHERE es.is_active = 1
                GROUP BY es.id, es.name
            """)
            
            sequences = []
            for row in await cursor.fetchall():
                name, total_leads, completed, emails_sent, emails_opened = row
                completion_rate = (completed / total_leads * 100) if total_leads > 0 else 0
                open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
                
                sequences.append({
                    "name": name,
                    "total_leads": total_leads,
                    "completion_rate": round(completion_rate, 1),
                    "open_rate": round(open_rate, 1),
                    "emails_sent": emails_sent
                })
            
            return JSONResponse(content={"sequences": sequences})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "Hunter Agency Dashboard",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat()
    }

# Lifecycle management
@app.on_event("startup")
async def startup():
    try:
        await database.connect()
        print("🚀 Dashboard connected to database")
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")

@app.on_event("shutdown") 
async def shutdown():
    try:
        await database.disconnect()
        print("👋 Dashboard disconnected from database")
    except Exception as e:
        print(f"Warning during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )

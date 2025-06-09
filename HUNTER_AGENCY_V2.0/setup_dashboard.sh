#!/bin/bash

# 🦁 Hunter Agency Dashboard - Auto Setup Script
# Usage: bash setup_dashboard.sh

echo "🦁 HUNTER AGENCY - Dashboard Setup Starting..."
echo "=================================================="

# Create dashboard directory if it doesn't exist
mkdir -p dashboard
cd dashboard

# 1. Create main.py (FastAPI Backend)
cat > main.py << 'ENDPY'
# 🦁 Hunter Agency - FastAPI Backend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import random
import json
from typing import List

app = FastAPI(title="Hunter Agency API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MockDB:
    def __init__(self):
        self.base_revenue = 247892
        self.base_dms = 8426
        self.base_creators = 24
        self.ai_conversion = 89.2
        
        self.creators_data = [
            {"name": "Sarah Moon", "avatar": "SM", "revenue": 47892, "subscribers": 2847, "growth": 18.5, "status": "active"},
            {"name": "Emma Vega", "avatar": "EV", "revenue": 39234, "subscribers": 2156, "growth": 24.3, "status": "active"},
            {"name": "Luna Rose", "avatar": "LR", "revenue": 34567, "subscribers": 1923, "growth": 15.7, "status": "active"},
            {"name": "Aria Dawn", "avatar": "AD", "revenue": 28134, "subscribers": 1654, "growth": 21.2, "status": "active"}
        ]

    def get_live_stats(self):
        revenue_variation = random.randint(-1000, 2000)
        dms_variation = random.randint(-50, 100)
        ai_variation = random.uniform(-0.5, 1.0)
        
        return {
            "totalRevenue": self.base_revenue + revenue_variation,
            "aiConversion": round(self.ai_conversion + ai_variation, 1),
            "dmsToday": self.base_dms + dms_variation,
            "activeCreators": self.base_creators,
            "revenueChange": "+32.4%",
            "aiChange": "+12.7%",
            "dmsChange": f"+{random.randint(100, 200)}",
            "creatorsChange": "+3",
            "timestamp": datetime.now().isoformat()
        }

db = MockDB()

@app.get("/")
async def root():
    return {"message": "🦁 Hunter Agency API", "status": "operational"}

@app.get("/api/stats")
async def get_stats():
    return JSONResponse(content=db.get_live_stats())

@app.get("/api/creators")
async def get_creators():
    creators = db.creators_data.copy()
    for creator in creators:
        creator["revenue"] += random.randint(-500, 1000)
        creator["subscribers"] += random.randint(-10, 50)
    return JSONResponse(content=creators)

@app.get("/api/charts")
async def get_charts():
    revenue_data = []
    for i in range(7):
        daily_revenue = 35000 + random.randint(-5000, 8000)
        revenue_data.append(round(daily_revenue / 1000, 1))
    
    return JSONResponse(content={
        "revenueChart": revenue_data,
        "platformChart": [65, 20, 10, 5]
    })

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
ENDPY

# 2. Create requirements.txt
cat > requirements.txt << 'ENDREQ'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.4.2
ENDREQ

# 3. Create start script
cat > start.sh << 'ENDSTART'
#!/bin/bash
echo "🦁 Starting Hunter Agency Dashboard..."
echo "======================================"

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀 Starting API server on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"

python main.py
ENDSTART

chmod +x start.sh

echo ""
echo "✅ Setup complete!"
echo "🚀 Run: cd dashboard && bash start.sh"
echo "📊 Then open http://localhost:8000 in browser!"

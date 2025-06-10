"""
🧪 Hunter Agency V2.2 - Tests
Tests for the main application functionality
"""

import pytest
import asyncio
from httpx import AsyncClient
from main import app, create_tables, database

@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "service" in data
    assert "version" in data

@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Hunter Agency" in data["message"]
    assert "endpoints" in data

@pytest.mark.asyncio
async def test_create_lead(client):
    """Test lead creation"""
    lead_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "industry": "tech",
        "source": "manual"
    }
    
    response = await client.post("/leads", json=lead_data)
    assert response.status_code == 200
    data = response.json()
    assert "lead" in data
    assert "message" in data
    assert data["lead"]["email"] == lead_data["email"]

@pytest.mark.asyncio
async def test_sequence_analytics(client):
    """Test sequence analytics endpoint"""
    response = await client.get("/sequences/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    assert "email_performance" in data

@pytest.mark.asyncio
async def test_sendgrid_webhook(client):
    """Test SendGrid webhook processing"""
    webhook_data = [
        {
            "email": "test@example.com",
            "event": "open",
            "timestamp": 1640995200,
            "sg_message_id": "test_message_id"
        }
    ]
    
    response = await client.post("/webhooks/sendgrid", json=webhook_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["events"] == 1

@pytest.mark.asyncio 
async def test_pipeline_leads_creation(client):
    """Test CRM pipeline lead creation"""
    lead_data = {
        "email": "pipeline.test@example.com",
        "first_name": "Pipeline",
        "last_name": "Test",
        "company": "Test Corp",
        "source": "linkedin",
        "industry": "saas"
    }
    
    response = await client.post("/api/pipeline/leads", json=lead_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == lead_data["email"]

@pytest.mark.asyncio
async def test_pipeline_analytics(client):
    """Test CRM pipeline analytics"""
    response = await client.get("/api/pipeline/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "leads_by_status" in data
    assert "opportunities_by_stage" in data
    assert "conversion_rate" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
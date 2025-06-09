import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crm.smart_pipeline.api.routes import app, get_db, Base
from crm.smart_pipeline.models import Lead

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# Dependency override


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_and_get_lead():
    response = client.post("/leads", json={"name": "Alice", "email": "a@example.com"})
    assert response.status_code == 201
    data = response.json()
    lead_id = data["id"]

    response = client.get(f"/leads/{lead_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"


def test_update_and_delete_lead():
    resp = client.post("/leads", json={"name": "Bob"})
    lead_id = resp.json()["id"]

    resp = client.put(f"/leads/{lead_id}", json={"name": "Bobby"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Bobby"

    resp = client.delete(f"/leads/{lead_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.get(f"/leads/{lead_id}")
    assert resp.status_code == 404


def test_pipeline_stage_creation():
    resp = client.post("/stages", json={"name": "Contacted", "order": 1})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Contacted"

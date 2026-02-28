import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# ── TEST DATABASE SETUP ───────────────────────────────────────────────────────
# Uses a separate test database — never touches production data
# DATABASE_URL is injected via environment variable in GitHub Actions

import os
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/testdb"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Replace the real DB session with a test DB session"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the DB dependency for all tests
app.dependency_overrides[get_db] = override_get_db

# Create test tables
Base.metadata.create_all(bind=engine)

# Test client — simulates HTTP requests without running a real server
client = TestClient(app)


# ── FIXTURES ──────────────────────────────────────────────────────────────────
@pytest.fixture
def sample_incident():
    """Creates a test incident and returns its data"""
    response = client.post("/incidents/", json={
        "title":       "Test Incident",
        "description": "This is a test incident",
        "severity":    "high",
        "source":      "manual"
    })
    return response.json()


# ── HEALTH CHECK TESTS ────────────────────────────────────────────────────────
def test_health_check():
    """App should return healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_check():
    """App + DB should both be ready"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


# ── CREATE INCIDENT TESTS ─────────────────────────────────────────────────────
def test_create_incident():
    """Should create a new incident and return 201"""
    response = client.post("/incidents/", json={
        "title":    "High CPU Alert",
        "severity": "critical",
        "source":   "alertmanager"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"]    == "High CPU Alert"
    assert data["severity"] == "critical"
    assert data["status"]   == "open"
    assert data["id"]       is not None


def test_create_incident_missing_title():
    """Should fail with 422 if title is missing"""
    response = client.post("/incidents/", json={
        "severity": "high"
    })
    assert response.status_code == 422


def test_create_incident_invalid_severity():
    """Should fail with 422 if severity is not in allowed values"""
    response = client.post("/incidents/", json={
        "title":    "Test",
        "severity": "extreme"          # not a valid SeverityLevel
    })
    assert response.status_code == 422


# ── LIST INCIDENTS TESTS ──────────────────────────────────────────────────────
def test_list_incidents(sample_incident):
    """Should return a list of incidents"""
    response = client.get("/incidents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_list_incidents_filter_by_status(sample_incident):
    """Should filter incidents by status"""
    response = client.get("/incidents/?status=open")
    assert response.status_code == 200
    for incident in response.json():
        assert incident["status"] == "open"


# ── GET INCIDENT TESTS ────────────────────────────────────────────────────────
def test_get_incident(sample_incident):
    """Should return a single incident by ID"""
    incident_id = sample_incident["id"]
    response = client.get(f"/incidents/{incident_id}")
    assert response.status_code == 200
    assert response.json()["id"] == incident_id


def test_get_incident_not_found():
    """Should return 404 for non-existent incident"""
    response = client.get("/incidents/99999")
    assert response.status_code == 404


# ── RESOLVE INCIDENT TESTS ────────────────────────────────────────────────────
def test_resolve_incident(sample_incident):
    """Should resolve an incident and set resolved_at timestamp"""
    incident_id = sample_incident["id"]
    response = client.put(f"/incidents/{incident_id}/resolve", json={
        "resolution_note": "Fixed by restarting the service"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"]      == "resolved"
    assert data["resolved_at"] is not None


def test_resolve_already_resolved(sample_incident):
    """Should return 400 if incident is already resolved"""
    incident_id = sample_incident["id"]

    # Resolve once
    client.put(f"/incidents/{incident_id}/resolve", json={})

    # Try to resolve again
    response = client.put(f"/incidents/{incident_id}/resolve", json={})
    assert response.status_code == 400


# ── ALERTMANAGER WEBHOOK TESTS ────────────────────────────────────────────────
def test_alertmanager_webhook():
    """Should auto-create incident from Alertmanager webhook payload"""
    payload = {
        "receiver": "incident-logger",
        "status":   "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighCPUUsage",
                    "severity":  "critical"
                },
                "annotations": {
                    "summary":     "CPU usage above 90%",
                    "description": "EC2 instance CPU has been above 90% for 5 minutes"
                }
            }
        ]
    }
    response = client.post("/incidents/webhook/alertmanager", json=payload)
    assert response.status_code == 200
    assert response.json()["incident_ids"] != []
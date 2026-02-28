from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.models import Incident, IncidentStatus, SeverityLevel
from app.schemas import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentResolve,
    AlertmanagerWebhook
)
from app.metrics import (
    incidents_created_total,
    incidents_resolved_total,
    incidents_open_gauge,
    incident_resolution_duration,
    alertmanager_webhooks_total
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


# ── CREATE ──────────────────────────────────────────────────────────────────
@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Manually create a new incident"""

    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Update Prometheus metrics
    incidents_created_total.labels(
        severity=incident.severity,
        source=incident.source or "manual"
    ).inc()

    incidents_open_gauge.labels(severity=incident.severity).inc()

    return incident


# ── LIST ALL ─────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[IncidentResponse])
def list_incidents(
    status: str = None,
    severity: str = None,
    db: Session = Depends(get_db)
):
    """List all incidents. Optional filters: ?status=open&severity=critical"""

    query = db.query(Incident)

    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)

    return query.order_by(Incident.created_at.desc()).all()


# ── GET ONE ──────────────────────────────────────────────────────────────────
@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get a single incident by ID"""

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    return incident


# ── UPDATE ───────────────────────────────────────────────────────────────────
@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db)):
    """Update incident fields — title, description, severity, status"""

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Only update fields that were actually sent
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)
    return incident


# ── RESOLVE ──────────────────────────────────────────────────────────────────
@router.put("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(incident_id: int, payload: IncidentResolve, db: Session = Depends(get_db)):
    """Resolve an incident and record resolution time for MTTR calculation"""

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    if incident.status == IncidentStatus.resolved:
        raise HTTPException(status_code=400, detail="Incident is already resolved")

    # Set resolved state
    incident.status     = IncidentStatus.resolved
    incident.resolved_at = datetime.now(timezone.utc)

    if payload.resolution_note:
        incident.description = f"{incident.description or ''}\n\nResolution: {payload.resolution_note}"

    db.commit()
    db.refresh(incident)

    # Calculate resolution duration in seconds for MTTR histogram
    duration = (incident.resolved_at - incident.created_at).total_seconds()

    # Update Prometheus metrics
    incidents_resolved_total.labels(severity=incident.severity).inc()
    incidents_open_gauge.labels(severity=incident.severity).dec()
    incident_resolution_duration.labels(severity=incident.severity).observe(duration)

    return incident


# ── DELETE ───────────────────────────────────────────────────────────────────
@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Delete an incident by ID"""

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    db.delete(incident)
    db.commit()


# ── ALERTMANAGER WEBHOOK ──────────────────────────────────────────────────────
@router.post("/webhook/alertmanager", status_code=status.HTTP_200_OK)
def alertmanager_webhook(payload: AlertmanagerWebhook, db: Session = Depends(get_db)):
    """
    Receives webhook from Alertmanager and auto-creates incidents.
    Add this URL to Alertmanager's receiver config:
    url: http://incident-logger:8000/incidents/webhook/alertmanager
    """

    alertmanager_webhooks_total.labels(status=payload.status).inc()

    created = []

    for alert in payload.alerts:
        if alert.status == "firing":
            # Map Prometheus severity label to our SeverityLevel enum
            raw_severity = alert.labels.get("severity", "medium").lower()
            severity = raw_severity if raw_severity in SeverityLevel.__members__ else "medium"

            incident = Incident(
                title      = alert.annotations.get("summary", alert.labels.get("alertname", "Unknown Alert")),
                description= alert.annotations.get("description", ""),
                severity   = severity,
                source     = "alertmanager",
                alert_name = alert.labels.get("alertname"),
                status     = IncidentStatus.open
            )

            db.add(incident)
            db.commit()
            db.refresh(incident)

            incidents_created_total.labels(severity=severity, source="alertmanager").inc()
            incidents_open_gauge.labels(severity=severity).inc()

            created.append(incident.id)

    return {"message": f"Created {len(created)} incident(s)", "incident_ids": created}
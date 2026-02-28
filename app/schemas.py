from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models import SeverityLevel, IncidentStatus


# --- REQUEST SCHEMAS ---
# These define what the API *accepts* (incoming data)

class IncidentCreate(BaseModel):
    """Schema for creating a new incident — POST /incidents"""
    title:       str          = Field(..., min_length=3, max_length=255, example="High CPU on EC2")
    description: Optional[str] = Field(None, example="CPU usage above 90% for 5 minutes")
    severity:    SeverityLevel = Field(default=SeverityLevel.medium, example="critical")
    source:      Optional[str] = Field(None, max_length=100, example="alertmanager")
    alert_name:  Optional[str] = Field(None, max_length=255, example="HighCPUUsage")


class IncidentUpdate(BaseModel):
    """Schema for updating an incident — PUT /incidents/{id}"""
    title:       Optional[str]           = Field(None, min_length=3, max_length=255)
    description: Optional[str]           = None
    severity:    Optional[SeverityLevel] = None
    status:      Optional[IncidentStatus] = None


# --- RESPONSE SCHEMAS ---
# These define what the API *returns* (outgoing data)

class IncidentResponse(BaseModel):
    """Full incident object returned by the API"""
    id:          int
    title:       str
    description: Optional[str]
    severity:    SeverityLevel
    status:      IncidentStatus
    source:      Optional[str]
    alert_name:  Optional[str]
    created_at:  datetime
    updated_at:  Optional[datetime]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True   # allows SQLAlchemy model → Pydantic conversion


class IncidentResolve(BaseModel):
    """Schema for resolving an incident — PUT /incidents/{id}/resolve"""
    resolution_note: Optional[str] = Field(None, example="Restarted the service, CPU back to normal")


# --- ALERTMANAGER WEBHOOK SCHEMA ---
# This is what Alertmanager sends when it fires an alert
# We parse this and auto-create an incident

class AlertmanagerAlert(BaseModel):
    status:      str
    labels:      dict
    annotations: dict

class AlertmanagerWebhook(BaseModel):
    """Incoming webhook payload from Alertmanager"""
    receiver:    str
    status:      str
    alerts:      list[AlertmanagerAlert]
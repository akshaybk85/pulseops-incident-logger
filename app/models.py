from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.database import Base


# Enum = a fixed set of allowed values
# This ensures severity can only be: low, medium, high, critical
class SeverityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# Status of the incident lifecycle
class IncidentStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"


# This class = the "incidents" table in PostgreSQL
# Every attribute = a column in the table
class Incident(Base):
    __tablename__ = "incidents"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity    = Column(Enum(SeverityLevel), default=SeverityLevel.medium, nullable=False)
    status      = Column(Enum(IncidentStatus), default=IncidentStatus.open, nullable=False)
    source      = Column(String(100), nullable=True)   # e.g. "alertmanager", "manual"
    alert_name  = Column(String(255), nullable=True)   # original alert name from Prometheus

    # Timestamps — set automatically by the database
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
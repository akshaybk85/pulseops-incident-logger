from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Basic liveness check.
    Used by: Docker HEALTHCHECK, Load balancer, CI/CD pipeline
    Returns 200 if app is running.
    """
    return {"status": "healthy"}


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check — verifies app AND database are both up.
    Used by: CI/CD pipeline post-deploy verification
    Returns 200 only if PostgreSQL connection is working.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "not ready",
            "database": "disconnected",
            "error": str(e)
        }
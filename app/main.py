from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.database import engine, Base
from app.routes import incidents, health
from app.config import settings

# Create all database tables on startup
# In production you'd use Alembic migrations instead
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Incident Logger",
    description="SRE Incident Management API — part of PulseOps observability platform",
    version="1.0.0"
)

# ── ROUTES ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(incidents.router)

# ── PROMETHEUS ───────────────────────────────────────────────────────────────
# Automatically exposes /metrics endpoint with HTTP request metrics
# Prometheus scrapes this endpoint every 15 seconds
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {
        "service": "incident-logger",
        "version": "1.0.0",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health"
    }
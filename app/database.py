from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create the PostgreSQL connection URL
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = settings.database_url

# Engine = actual connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal = a factory that creates database sessions
# Each request gets its own session, then closes it
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = parent class for all our database models (tables)
Base = declarative_base()


# Dependency — used in every route that needs DB access
# FastAPI calls this automatically, opens a session, then closes it after the request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
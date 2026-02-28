from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/incidentdb"

    # App
    app_env: str = "development"   # development | production

    class Config:
        env_file = ".env"          # reads from .env file automatically


# Single instance used across the whole app
settings = Settings()
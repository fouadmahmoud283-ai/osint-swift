"""Configuration for SWIFT API."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://swift:swift123@localhost:5432/swift",
        description="PostgreSQL connection string"
    )
    
    # Ingestion Service
    ingestion_service_url: str = Field(
        default="http://swift-ingestion-worker:8001",
        description="Ingestion service base URL"
    )
    
    # Celery/Redis
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    
    # Application
    environment: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Log level")


settings = Settings()

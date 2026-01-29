"""Configuration management for SWIFT Ingestion Service."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://swift:swift123@localhost:5432/swift_db",
        description="PostgreSQL connection string"
    )

    # Object Storage (S3/MinIO)
    s3_endpoint_url: Optional[str] = Field(
        default="http://localhost:9000",
        description="S3-compatible storage endpoint"
    )
    s3_access_key: str = Field(default="minioadmin", description="S3 access key")
    s3_secret_key: str = Field(default="minioadmin", description="S3 secret key")
    s3_bucket_name: str = Field(default="swift-evidence", description="S3 bucket name")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    # Redis/Celery
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )

    # API Keys
    opencorporates_api_key: Optional[str] = Field(
        default=None,
        description="OpenCorporates API key"
    )
    news_api_key: Optional[str] = Field(
        default=None,
        description="News API key"
    )
    apify_api_token: Optional[str] = Field(
        default=None,
        description="OSINT automation API token"
    )
    osint_actor_id: Optional[str] = Field(
        default=None,
        description="OSINT automation actor id"
    )

    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")
    max_workers: int = Field(default=4, description="Maximum number of workers")
    ingestion_timeout: int = Field(
        default=300,
        description="Ingestion timeout in seconds"
    )

    # Evidence Storage
    evidence_retention_days: int = Field(
        default=365,
        description="Evidence retention period in days"
    )
    max_file_size_mb: int = Field(
        default=100,
        description="Maximum file size for evidence in MB"
    )


# Global settings instance
settings = Settings()

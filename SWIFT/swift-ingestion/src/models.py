"""Core data models for SWIFT Ingestion Service."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class JobStatus(str, Enum):
    """Status of an ingestion job."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some items succeeded, some failed
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Type of data source."""
    
    OPENCORPORATES = "opencorporates"
    NEWS_API = "news_api"
    OSINT_SEARCH = "osint_search"
    RSS_FEED = "rss_feed"
    WEB_SCRAPER = "web_scraper"
    MANUAL_UPLOAD = "manual_upload"


class EvidenceType(str, Enum):
    """Type of evidence document."""
    
    COMPANY_RECORD = "company_record"
    NEWS_ARTICLE = "news_article"
    LEGAL_DOCUMENT = "legal_document"
    WEB_PAGE = "web_page"
    PDF_DOCUMENT = "pdf_document"
    IMAGE = "image"
    RAW_DATA = "raw_data"


class IngestionJobCreate(BaseModel):
    """Request model for creating an ingestion job."""
    
    model_config = ConfigDict(from_attributes=True)
    
    source_type: SourceType
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific parameters (e.g., search query, company name)"
    )
    case_id: Optional[UUID] = Field(
        default=None,
        description="Associated case ID if this ingestion is part of an investigation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class IngestionJob(BaseModel):
    """Ingestion job model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    status: JobStatus = JobStatus.PENDING
    parameters: Dict[str, Any] = Field(default_factory=dict)
    case_id: Optional[UUID] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    
    # Error tracking
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    celery_task_id: Optional[str] = None


class EvidenceDocument(BaseModel):
    """Evidence document model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    
    # Source Information
    source_type: SourceType
    source_url: Optional[str] = None
    source_identifier: Optional[str] = Field(
        default=None,
        description="Original ID from source system"
    )
    
    # Storage
    object_key: str = Field(description="S3 object key")
    checksum: str = Field(description="SHA-256 checksum of content")
    file_size_bytes: int
    content_type: str = Field(default="application/json")
    
    # Classification
    evidence_type: EvidenceType
    
    # Timestamps
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    source_timestamp: Optional[datetime] = Field(
        default=None,
        description="Original timestamp from source"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific metadata"
    )
    
    # Chain of custody
    extraction_version: Optional[str] = None
    processing_status: str = "raw"  # raw, extracted, processed


class ConnectorConfig(BaseModel):
    """Configuration for a data connector."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    source_type: SourceType
    enabled: bool = True
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Connector-specific configuration"
    )


class IngestionJobStats(BaseModel):
    """Statistics for an ingestion job."""
    
    job_id: UUID
    status: JobStatus
    duration_seconds: Optional[float] = None
    total_items: int
    successful_items: int
    failed_items: int
    avg_item_size_bytes: Optional[float] = None
    total_size_bytes: int = 0

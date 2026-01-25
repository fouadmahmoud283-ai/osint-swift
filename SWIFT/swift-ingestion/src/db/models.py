"""SQLAlchemy database models for SWIFT Ingestion Service."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Enum as SQLEnum,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from ..models import EvidenceType, JobStatus, SourceType

Base = declarative_base()


class IngestionJobDB(Base):
    """Database model for ingestion jobs."""
    
    __tablename__ = "ingestion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_type = Column(SQLEnum(SourceType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    parameters = Column(JSON, nullable=False, default=dict)
    case_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    total_items = Column(Integer, nullable=False, default=0)
    successful_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=False, default=dict)
    celery_task_id = Column(String(255), nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<IngestionJob(id={self.id}, source={self.source_type}, status={self.status})>"


class EvidenceDocumentDB(Base):
    """Database model for evidence documents."""
    
    __tablename__ = "evidence_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Source Information
    source_type = Column(SQLEnum(SourceType), nullable=False, index=True)
    source_url = Column(Text, nullable=True)
    source_identifier = Column(String(500), nullable=True, index=True)
    
    # Storage
    object_key = Column(String(500), nullable=False, unique=True)
    checksum = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False, default="application/json")
    
    # Classification
    evidence_type = Column(SQLEnum(EvidenceType), nullable=False, index=True)
    
    # Timestamps
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source_timestamp = Column(DateTime, nullable=True, index=True)
    
    # Metadata
    metadata = Column(JSON, nullable=False, default=dict)
    
    # Chain of custody
    extraction_version = Column(String(50), nullable=True)
    processing_status = Column(String(50), nullable=False, default="raw", index=True)
    
    def __repr__(self) -> str:
        return f"<EvidenceDocument(id={self.id}, type={self.evidence_type}, job={self.job_id})>"


class ConnectorConfigDB(Base):
    """Database model for connector configurations."""
    
    __tablename__ = "connector_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(SQLEnum(SourceType), nullable=False, unique=True)
    enabled = Column(Integer, nullable=False, default=1)  # SQLite compatible boolean
    rate_limit_per_minute = Column(Integer, nullable=False, default=60)
    timeout_seconds = Column(Integer, nullable=False, default=30)
    retry_attempts = Column(Integer, nullable=False, default=3)
    config = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ConnectorConfig(name={self.name}, type={self.source_type})>"

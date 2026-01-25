"""Evidence repository for database operations."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..db.models import EvidenceDocumentDB, IngestionJobDB
from ..models import (
    EvidenceDocument,
    EvidenceType,
    IngestionJob,
    IngestionJobStats,
    JobStatus,
    SourceType,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JobRepository:
    """Repository for ingestion job database operations."""
    
    @staticmethod
    def create_job(session: Session, job: IngestionJob) -> IngestionJobDB:
        """Create a new ingestion job."""
        db_job = IngestionJobDB(
            id=job.id,
            source_type=job.source_type,
            status=job.status,
            parameters=job.parameters,
            case_id=job.case_id,
            metadata_json=job.metadata,
            celery_task_id=job.celery_task_id,
        )
        session.add(db_job)
        session.flush()
        
        logger.info(
            f"Created job {db_job.id}",
            extra={'job_id': str(db_job.id), 'source': job.source_type.value}
        )
        
        return db_job
    
    @staticmethod
    def get_job(session: Session, job_id: UUID) -> Optional[IngestionJobDB]:
        """Get job by ID."""
        return session.query(IngestionJobDB).filter(IngestionJobDB.id == job_id).first()
    
    @staticmethod
    def update_job_status(
        session: Session,
        job_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None,
        error_details: Optional[dict] = None
    ) -> None:
        """Update job status."""
        job = session.query(IngestionJobDB).filter(IngestionJobDB.id == job_id).first()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        job.status = status
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        
        if status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.PARTIAL]:
            job.completed_at = datetime.utcnow()
        
        if error_message:
            job.error_message = error_message
            job.error_details = error_details
        
        session.flush()
        
        logger.info(
            f"Updated job {job_id} status to {status.value}",
            extra={'job_id': str(job_id), 'status': status.value}
        )
    
    @staticmethod
    def update_job_counts(
        session: Session,
        job_id: UUID,
        total: int,
        successful: int,
        failed: int
    ) -> None:
        """Update job item counts."""
        job = session.query(IngestionJobDB).filter(IngestionJobDB.id == job_id).first()
        
        if job:
            job.total_items = total
            job.successful_items = successful
            job.failed_items = failed
            session.flush()
    
    @staticmethod
    def list_jobs(
        session: Session,
        status: Optional[JobStatus] = None,
        source_type: Optional[SourceType] = None,
        case_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[IngestionJobDB]:
        """List jobs with optional filters."""
        query = session.query(IngestionJobDB)
        
        if status:
            query = query.filter(IngestionJobDB.status == status)
        if source_type:
            query = query.filter(IngestionJobDB.source_type == source_type)
        if case_id:
            query = query.filter(IngestionJobDB.case_id == case_id)
        
        return query.order_by(desc(IngestionJobDB.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_job_stats(session: Session, job_id: UUID) -> Optional[IngestionJobStats]:
        """Get job statistics."""
        job = session.query(IngestionJobDB).filter(IngestionJobDB.id == job_id).first()
        
        if not job:
            return None
        
        # Calculate duration
        duration = None
        if job.started_at and job.completed_at:
            duration = (job.completed_at - job.started_at).total_seconds()
        
        # Get evidence stats
        evidence_stats = session.query(
            func.coalesce(func.avg(EvidenceDocumentDB.file_size_bytes), 0).label('avg_size'),
            func.coalesce(func.sum(EvidenceDocumentDB.file_size_bytes), 0).label('total_size')
        ).filter(EvidenceDocumentDB.job_id == job_id).first()
        
        return IngestionJobStats(
            job_id=job.id,
            status=job.status,
            duration_seconds=duration,
            total_items=job.total_items,
            successful_items=job.successful_items,
            failed_items=job.failed_items,
            avg_item_size_bytes=float(evidence_stats.avg_size) if evidence_stats else None,
            total_size_bytes=int(evidence_stats.total_size) if evidence_stats else 0
        )


class EvidenceRepository:
    """Repository for evidence document database operations."""
    
    @staticmethod
    def create_evidence(session: Session, evidence: EvidenceDocument) -> EvidenceDocumentDB:
        """Create a new evidence document record."""
        db_evidence = EvidenceDocumentDB(
            id=evidence.id,
            job_id=evidence.job_id,
            source_type=evidence.source_type,
            source_url=evidence.source_url,
            source_identifier=evidence.source_identifier,
            object_key=evidence.object_key,
            checksum=evidence.checksum,
            file_size_bytes=evidence.file_size_bytes,
            content_type=evidence.content_type,
            evidence_type=evidence.evidence_type,
            source_timestamp=evidence.source_timestamp,
            metadata_json=evidence.metadata,
            processing_status=evidence.processing_status,
        )
        session.add(db_evidence)
        session.flush()
        
        logger.info(
            f"Created evidence {db_evidence.id}",
            extra={
                'evidence_id': str(db_evidence.id),
                'job_id': str(evidence.job_id),
                'type': evidence.evidence_type.value
            }
        )
        
        return db_evidence
    
    @staticmethod
    def get_evidence(session: Session, evidence_id: UUID) -> Optional[EvidenceDocumentDB]:
        """Get evidence by ID."""
        return session.query(EvidenceDocumentDB).filter(
            EvidenceDocumentDB.id == evidence_id
        ).first()
    
    @staticmethod
    def list_evidence_by_job(
        session: Session,
        job_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvidenceDocumentDB]:
        """List evidence documents for a job."""
        return session.query(EvidenceDocumentDB).filter(
            EvidenceDocumentDB.job_id == job_id
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_evidence_by_checksum(
        session: Session,
        checksum: str
    ) -> Optional[EvidenceDocumentDB]:
        """Find evidence by checksum (for deduplication)."""
        return session.query(EvidenceDocumentDB).filter(
            EvidenceDocumentDB.checksum == checksum
        ).first()

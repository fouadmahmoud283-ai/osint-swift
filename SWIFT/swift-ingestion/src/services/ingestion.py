"""Ingestion service orchestrating the data collection process."""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..connectors import ConnectorRegistry
from ..db import get_db
from ..models import (
    EvidenceDocument,
    EvidenceType,
    IngestionJob,
    IngestionJobCreate,
    JobStatus,
    SourceType,
)
from ..storage import EvidenceRepository, JobRepository, object_storage
from ..utils.logging import get_logger

logger = get_logger(__name__)


class IngestionService:
    """
    Core ingestion service.
    
    Orchestrates the process of:
    1. Creating ingestion jobs
    2. Fetching data from connectors
    3. Storing evidence in object storage
    4. Recording metadata in database
    5. Tracking job progress and failures
    """
    
    def __init__(self):
        self.job_repo = JobRepository()
        self.evidence_repo = EvidenceRepository()
    
    def create_job(self, job_create: IngestionJobCreate) -> IngestionJob:
        """
        Create a new ingestion job.
        
        Args:
            job_create: Job creation parameters
        
        Returns:
            Created IngestionJob
        """
        job = IngestionJob(
            source_type=job_create.source_type,
            parameters=job_create.parameters,
            case_id=job_create.case_id,
            metadata=job_create.metadata,
        )
        
        with get_db() as session:
            self.job_repo.create_job(session, job)
        
        logger.info(
            f"Created ingestion job {job.id}",
            extra={
                'job_id': str(job.id),
                'source_type': job.source_type.value,
                'case_id': str(job.case_id) if job.case_id else None
            }
        )
        
        return job
    
    async def execute_job(self, job_id: UUID) -> None:
        """
        Execute an ingestion job.
        
        This is the main orchestration method that:
        1. Gets the connector
        2. Fetches data
        3. Stores evidence
        4. Updates job status
        
        Args:
            job_id: ID of the job to execute
        """
        logger.info(f"Starting execution of job {job_id}", extra={'job_id': str(job_id)})
        
        # Get job from database
        with get_db() as session:
            db_job = self.job_repo.get_job(session, job_id)
            if not db_job:
                logger.error(f"Job {job_id} not found")
                return
            
            job = IngestionJob.model_validate(db_job)
        
        try:
            # Update status to running
            with get_db() as session:
                self.job_repo.update_job_status(session, job_id, JobStatus.RUNNING)
            
            # Get connector configuration
            connector_config = self._get_connector_config(job.source_type)
            
            # Create connector instance
            connector = ConnectorRegistry.get_connector(job.source_type, connector_config)
            
            # Fetch and store data
            total_items = 0
            successful_items = 0
            failed_items = 0
            
            async for result in connector.fetch(job.parameters):
                total_items += 1
                
                try:
                    # Store evidence
                    evidence_id = await self._store_evidence(
                        job_id=job_id,
                        source_type=job.source_type,
                        result=result
                    )
                    
                    successful_items += 1
                    
                    logger.info(
                        f"Stored evidence {evidence_id}",
                        extra={
                            'job_id': str(job_id),
                            'evidence_id': str(evidence_id),
                            'total': total_items,
                            'successful': successful_items
                        }
                    )
                    
                except Exception as e:
                    failed_items += 1
                    logger.error(
                        f"Failed to store evidence item {total_items}: {e}",
                        extra={'job_id': str(job_id), 'error': str(e)}
                    )
            
            # Close connector if needed
            if hasattr(connector, 'close'):
                await connector.close()
            
            # Update job counts
            with get_db() as session:
                self.job_repo.update_job_counts(
                    session, job_id, total_items, successful_items, failed_items
                )
            
            # Determine final status
            if failed_items == 0:
                final_status = JobStatus.SUCCESS
            elif successful_items > 0:
                final_status = JobStatus.PARTIAL
            else:
                final_status = JobStatus.FAILED
            
            # Update final status
            with get_db() as session:
                self.job_repo.update_job_status(session, job_id, final_status)
            
            logger.info(
                f"Completed job {job_id}",
                extra={
                    'job_id': str(job_id),
                    'status': final_status.value,
                    'total': total_items,
                    'successful': successful_items,
                    'failed': failed_items
                }
            )
            
        except Exception as e:
            error_msg = f"Job execution failed: {str(e)}"
            logger.error(error_msg, extra={'job_id': str(job_id), 'error': str(e)})
            
            # Update job as failed
            with get_db() as session:
                self.job_repo.update_job_status(
                    session,
                    job_id,
                    JobStatus.FAILED,
                    error_message=error_msg,
                    error_details={'exception': str(e)}
                )
    
    async def _store_evidence(
        self,
        job_id: UUID,
        source_type: SourceType,
        result
    ) -> UUID:
        """
        Store evidence document.
        
        Args:
            job_id: Ingestion job ID
            source_type: Source type
            result: ConnectorResult
        
        Returns:
            Evidence document ID
        """
        # Create evidence document
        evidence = EvidenceDocument(
            job_id=job_id,
            source_type=source_type,
            source_url=result.source_url,
            source_identifier=result.source_identifier,
            evidence_type=result.evidence_type,
            source_timestamp=result.source_timestamp,
            metadata=result.metadata,
            object_key="",  # Will be set below
            checksum="",    # Will be set below
            file_size_bytes=0,  # Will be set below
        )
        
        # Generate object key
        evidence.object_key = object_storage.generate_object_key(
            job_id=job_id,
            source_type=source_type.value,
            evidence_id=evidence.id,
            extension="json"
        )
        
        # Store in object storage
        checksum, file_size = object_storage.store_json_evidence(
            object_key=evidence.object_key,
            data=result.data,
            metadata={
                'job_id': str(job_id),
                'source_type': source_type.value,
                'evidence_type': result.evidence_type.value,
            }
        )
        
        evidence.checksum = checksum
        evidence.file_size_bytes = file_size
        
        # Store metadata in database
        with get_db() as session:
            self.evidence_repo.create_evidence(session, evidence)
        
        return evidence.id
    
    def _get_connector_config(self, source_type: SourceType) -> dict:
        """
        Get connector configuration from database or environment.
        
        Args:
            source_type: Type of connector
        
        Returns:
            Connector configuration dictionary
        """
        from ..config import settings
        
        # For now, use settings directly
        # In the future, this could query ConnectorConfigDB
        config = {
            'rate_limit_per_minute': 60,
            'timeout_seconds': 30,
        }
        
        if source_type == SourceType.OPENCORPORATES:
            if not settings.opencorporates_api_key:
                raise ValueError("OpenCorporates API key not configured")
            config['api_key'] = settings.opencorporates_api_key
        
        elif source_type == SourceType.NEWS_API:
            if not settings.news_api_key:
                raise ValueError("News API key not configured. Get one free at https://newsapi.org/register")
            config['api_key'] = settings.news_api_key
            config['rate_limit_per_minute'] = 6  # Free tier: 100 requests per 15 min
        
        return config
    
    def get_job(self, job_id: UUID) -> Optional[IngestionJob]:
        """Get job by ID."""
        with get_db() as session:
            db_job = self.job_repo.get_job(session, job_id)
            if db_job:
                return IngestionJob.model_validate(db_job)
        return None
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        source_type: Optional[SourceType] = None,
        case_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[IngestionJob]:
        """List jobs with optional filters."""
        with get_db() as session:
            db_jobs = self.job_repo.list_jobs(
                session, status, source_type, case_id, limit, offset
            )
            return [IngestionJob.model_validate(job) for job in db_jobs]
    
    def get_job_stats(self, job_id: UUID):
        """Get job statistics."""
        with get_db() as session:
            return self.job_repo.get_job_stats(session, job_id)

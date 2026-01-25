"""Client for communicating with ingestion service."""

from typing import Optional
from uuid import UUID

# This will import from swift-ingestion
# In a real deployment, this would be a separate package or use API calls
import sys
from pathlib import Path

# Add swift-ingestion to path
ingestion_path = Path(__file__).parent.parent.parent.parent / "swift-ingestion" / "src"
sys.path.insert(0, str(ingestion_path))

from models import IngestionJobCreate, JobStatus, SourceType
from services import IngestionService, celery_app


class IngestionClient:
    """
    Client for interacting with the ingestion service.
    
    In a microservices architecture, this would make HTTP calls.
    For now, it directly uses the ingestion service.
    """
    
    def __init__(self):
        self.service = IngestionService()
    
    async def create_job(
        self,
        source_type: str,
        parameters: dict,
        case_id: Optional[UUID] = None,
        metadata: dict = None
    ):
        """Create a new ingestion job and queue it for execution."""
        # Convert string to enum
        try:
            source_enum = SourceType(source_type)
        except ValueError:
            raise ValueError(f"Invalid source type: {source_type}")
        
        # Create job
        job_create = IngestionJobCreate(
            source_type=source_enum,
            parameters=parameters,
            case_id=case_id,
            metadata=metadata or {}
        )
        
        job = self.service.create_job(job_create)
        
        # Queue job for asynchronous execution
        task = celery_app.send_task(
            'tasks.execute_ingestion_job',
            args=[str(job.id)]
        )
        
        # Update job with Celery task ID
        from db import get_db
        from storage import JobRepository
        
        with get_db() as session:
            db_job = JobRepository.get_job(session, job.id)
            if db_job:
                db_job.celery_task_id = task.id
                session.flush()
        
        job.celery_task_id = task.id
        
        return job
    
    async def get_job(self, job_id: UUID):
        """Get job by ID."""
        return self.service.get_job(job_id)
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        case_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """List jobs with filters."""
        status_enum = JobStatus(status) if status else None
        source_enum = SourceType(source_type) if source_type else None
        
        return self.service.list_jobs(
            status=status_enum,
            source_type=source_enum,
            case_id=case_id,
            limit=limit,
            offset=offset
        )
    
    async def get_job_stats(self, job_id: UUID):
        """Get job statistics."""
        return self.service.get_job_stats(job_id)

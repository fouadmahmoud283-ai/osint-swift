"""Celery worker configuration and tasks."""

import asyncio
from uuid import UUID

from celery import Celery
from celery.signals import worker_process_init

from ..config import settings
from ..db import init_db
from ..utils.logging import configure_logging, get_logger

# Create Celery app
celery_app = Celery(
    'swift-ingestion',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.ingestion_timeout,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

logger = get_logger(__name__)


@worker_process_init.connect
def init_worker(**kwargs):
    """Initialize worker process."""
    configure_logging()
    init_db()
    logger.info("Worker process initialized")


@celery_app.task(name='tasks.execute_ingestion_job', bind=True)
def execute_ingestion_job(self, job_id: str) -> dict:
    """
    Execute an ingestion job asynchronously.
    
    Args:
        job_id: UUID of the ingestion job
    
    Returns:
        Job result dictionary
    """
    from .ingestion import IngestionService
    
    job_uuid = UUID(job_id)
    
    logger.info(
        f"Starting ingestion job {job_id}",
        extra={'job_id': job_id, 'task_id': self.request.id}
    )
    
    try:
        # Create service and execute job
        service = IngestionService()
        
        # Run async execution in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(service.execute_job(job_uuid))
        finally:
            loop.close()
        
        # Get final job status
        job = service.get_job(job_uuid)
        
        result = {
            'job_id': job_id,
            'status': job.status.value if job else 'unknown',
            'total_items': job.total_items if job else 0,
            'successful_items': job.successful_items if job else 0,
            'failed_items': job.failed_items if job else 0,
        }
        
        logger.info(
            f"Completed ingestion job {job_id}",
            extra={'job_id': job_id, 'result': result}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to execute ingestion job {job_id}: {e}",
            extra={'job_id': job_id, 'error': str(e)}
        )
        raise

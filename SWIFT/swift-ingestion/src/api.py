"""FastAPI app for SWIFT Ingestion Service."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from .db import get_db
from .models import IngestionJobCreate, IngestionJobStats, JobStatus, SourceType
from .services.ingestion import IngestionService
from .storage import JobRepository
from .utils.logging import get_logger
from .services.worker import celery_app

logger = get_logger(__name__)

app = FastAPI(
    title="SWIFT Ingestion Service",
    description="Ingestion service API for job orchestration",
    version="0.1.0",
)

job_repo = JobRepository()
service = IngestionService()


def _serialize_job_db(job) -> dict:
    return {
        "id": str(job.id),
        "source_type": job.source_type.value,
        "status": job.status.value,
        "parameters": job.parameters,
        "case_id": str(job.case_id) if job.case_id else None,
        "created_at": job.created_at.isoformat() if isinstance(job.created_at, datetime) else job.created_at,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "total_items": job.total_items,
        "successful_items": job.successful_items,
        "failed_items": job.failed_items,
        "error_message": job.error_message,
        "metadata": job.metadata_json,
        "celery_task_id": job.celery_task_id,
    }


def _serialize_stats(stats: IngestionJobStats) -> dict:
    return {
        "job_id": str(stats.job_id),
        "status": stats.status.value,
        "duration_seconds": stats.duration_seconds,
        "total_items": stats.total_items,
        "successful_items": stats.successful_items,
        "failed_items": stats.failed_items,
        "avg_item_size_bytes": stats.avg_item_size_bytes,
        "total_size_bytes": stats.total_size_bytes,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "swift-ingestion"}


@app.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(request: IngestionJobCreate):
    try:
        job = service.create_job(request)
        task = celery_app.send_task("tasks.execute_ingestion_job", args=[str(job.id)])

        with get_db() as session:
            db_job = job_repo.get_job(session, job.id)
            if db_job:
                db_job.celery_task_id = task.id
                session.flush()
            else:
                raise HTTPException(status_code=404, detail=f"Job {job.id} not found")

        return _serialize_job_db(db_job)
    except Exception as exc:
        logger.error("Failed to create job", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ingestion job: {str(exc)}",
        )


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    with get_db() as session:
        db_job = job_repo.get_job(session, job_uuid)
        if not db_job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _serialize_job_db(db_job)


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    case_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    try:
        status_enum = JobStatus(status) if status else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")

    try:
        source_enum = SourceType(source_type) if source_type else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source_type value")

    case_uuid = None
    if case_id:
        try:
            case_uuid = UUID(case_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid case_id value")

    with get_db() as session:
        jobs = job_repo.list_jobs(
            session,
            status=status_enum,
            source_type=source_enum,
            case_id=case_uuid,
            limit=limit,
            offset=offset,
        )

    return [_serialize_job_db(job) for job in jobs]


@app.get("/jobs/{job_id}/stats")
async def get_job_stats(job_id: str):
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    with get_db() as session:
        stats = job_repo.get_job_stats(session, job_uuid)
        if not stats:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return _serialize_stats(stats)

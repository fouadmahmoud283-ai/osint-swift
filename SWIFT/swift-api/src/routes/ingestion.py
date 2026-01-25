"""API routes for ingestion management."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services.ingestion_client import IngestionClient

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# Initialize client
ingestion_client = IngestionClient()


class CreateJobRequest(BaseModel):
    """Request to create an ingestion job."""
    
    source_type: str = Field(..., description="Source type (e.g., 'opencorporates')")
    parameters: dict = Field(..., description="Source-specific parameters")
    case_id: Optional[str] = Field(None, description="Associated case ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class JobResponse(BaseModel):
    """Ingestion job response."""
    
    id: str
    source_type: str
    status: str
    parameters: dict
    case_id: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    total_items: int
    successful_items: int
    failed_items: int
    error_message: Optional[str]
    metadata: dict
    celery_task_id: Optional[str]


class JobStatsResponse(BaseModel):
    """Job statistics response."""
    
    job_id: str
    status: str
    duration_seconds: Optional[float]
    total_items: int
    successful_items: int
    failed_items: int
    avg_item_size_bytes: Optional[float]
    total_size_bytes: int


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_ingestion_job(request: CreateJobRequest):
    """
    Create a new ingestion job.
    
    The job will be queued for asynchronous execution.
    """
    try:
        job = await ingestion_client.create_job(
            source_type=request.source_type,
            parameters=request.parameters,
            case_id=UUID(request.case_id) if request.case_id else None,
            metadata=request.metadata
        )
        
        return JobResponse(
            id=str(job.id),
            source_type=job.source_type.value,
            status=job.status.value,
            parameters=job.parameters,
            case_id=str(job.case_id) if job.case_id else None,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            total_items=job.total_items,
            successful_items=job.successful_items,
            failed_items=job.failed_items,
            error_message=job.error_message,
            metadata=job.metadata,
            celery_task_id=job.celery_task_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ingestion job: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_ingestion_job(job_id: str):
    """Get ingestion job by ID."""
    try:
        job_uuid = UUID(job_id)
        job = await ingestion_client.get_job(job_uuid)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return JobResponse(
            id=str(job.id),
            source_type=job.source_type.value,
            status=job.status.value,
            parameters=job.parameters,
            case_id=str(job.case_id) if job.case_id else None,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            total_items=job.total_items,
            successful_items=job.successful_items,
            failed_items=job.failed_items,
            error_message=job.error_message,
            metadata=job.metadata,
            celery_task_id=job.celery_task_id
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )


@router.get("/jobs", response_model=List[JobResponse])
async def list_ingestion_jobs(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    case_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List ingestion jobs with optional filters."""
    try:
        jobs = await ingestion_client.list_jobs(
            status=status,
            source_type=source_type,
            case_id=UUID(case_id) if case_id else None,
            limit=limit,
            offset=offset
        )
        
        return [
            JobResponse(
                id=str(job.id),
                source_type=job.source_type.value,
                status=job.status.value,
                parameters=job.parameters,
                case_id=str(job.case_id) if job.case_id else None,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                total_items=job.total_items,
                successful_items=job.successful_items,
                failed_items=job.failed_items,
                error_message=job.error_message,
                metadata=job.metadata,
                celery_task_id=job.celery_task_id
            )
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}/stats", response_model=JobStatsResponse)
async def get_job_stats(job_id: str):
    """Get detailed statistics for an ingestion job."""
    try:
        job_uuid = UUID(job_id)
        stats = await ingestion_client.get_job_stats(job_uuid)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return JobStatsResponse(
            job_id=str(stats.job_id),
            status=stats.status.value,
            duration_seconds=stats.duration_seconds,
            total_items=stats.total_items,
            successful_items=stats.successful_items,
            failed_items=stats.failed_items,
            avg_item_size_bytes=stats.avg_item_size_bytes,
            total_size_bytes=stats.total_size_bytes
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )


@router.get("/sources")
async def list_sources():
    """List available data sources."""
    return {
        "sources": [
            {
                "type": "opencorporates",
                "name": "OpenCorporates",
                "description": "Company registration data from 140+ jurisdictions",
                "free_tier": False,
                "parameters": {
                    "company_name": "string (required)",
                    "jurisdiction_code": "string (optional, e.g., 'us_de', 'gb')",
                    "include_inactive": "boolean (optional)"
                },
                "example": {
                    "company_name": "Tesla Inc",
                    "jurisdiction_code": "us_de"
                }
            },
            {
                "type": "news_api",
                "name": "News API",
                "description": "News articles from 80,000+ sources worldwide",
                "free_tier": True,
                "rate_limit": "1000 requests/day",
                "parameters": {
                    "query": "string (required) - search query",
                    "from_date": "string (optional, YYYY-MM-DD)",
                    "to_date": "string (optional, YYYY-MM-DD)",
                    "language": "string (optional, e.g., 'en', 'es')",
                    "sort_by": "string (optional: relevancy, popularity, publishedAt)",
                    "domains": "string (optional, comma-separated)",
                    "max_articles": "integer (optional, default 100)"
                },
                "example": {
                    "query": "Tesla OR Elon Musk",
                    "from_date": "2024-01-01",
                    "language": "en",
                    "sort_by": "relevancy",
                    "max_articles": 50
                }
            }
        ]
    }

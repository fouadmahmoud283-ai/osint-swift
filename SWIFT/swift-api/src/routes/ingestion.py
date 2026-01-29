"""API routes for ingestion management."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services.ingestion_client import IngestionClient

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

# Initialize client
ingestion_client = IngestionClient()


def _job_from_payload(job: dict) -> "JobResponse":
    return JobResponse(
        id=str(job.get("id")),
        source_type=job.get("source_type"),
        status=job.get("status"),
        parameters=job.get("parameters", {}),
        case_id=job.get("case_id"),
        created_at=job.get("created_at"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        total_items=job.get("total_items", 0),
        successful_items=job.get("successful_items", 0),
        failed_items=job.get("failed_items", 0),
        error_message=job.get("error_message"),
        metadata=job.get("metadata", {}),
        celery_task_id=job.get("celery_task_id"),
    )


def _stats_from_payload(stats: dict) -> "JobStatsResponse":
    return JobStatsResponse(
        job_id=str(stats.get("job_id")),
        status=stats.get("status"),
        duration_seconds=stats.get("duration_seconds"),
        total_items=stats.get("total_items", 0),
        successful_items=stats.get("successful_items", 0),
        failed_items=stats.get("failed_items", 0),
        avg_item_size_bytes=stats.get("avg_item_size_bytes"),
        total_size_bytes=stats.get("total_size_bytes", 0),
    )


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
        
        return _job_from_payload(job)
        
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
        
        return _job_from_payload(job)
        
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
        
        return [_job_from_payload(job) for job in jobs]
        
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
        
        return _stats_from_payload(stats)
        
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
            },
            {
                "type": "osint_search",
                "name": "OSINT Search",
                "description": "Deep digital footprint discovery and profile scanning",
                "free_tier": False,
                "parameters": {
                    "searchQuery": "string (required)",
                    "searchType": "string (required: email, username, phone)",
                    "scanDepth": "string (optional: standard, deep)",
                    "categories": "array (optional)",
                    "exportFormats": "array (optional, default ['json'])",
                    "extractData": "boolean (optional)",
                    "recursiveSearch": "boolean (optional)",
                    "reportSorting": "string (optional)",
                    "timeout": "integer (optional, minutes)",
                    "maxConcurrency": "integer (optional)",
                    "retries": "integer (optional)",
                    "printErrors": "boolean (optional)",
                    "proxyConfiguration": "object (optional)"
                },
                "example": {
                    "searchQuery": "fouadmahmoud281@gmail.com",
                    "searchType": "email",
                    "scanDepth": "deep",
                    "categories": [
                        "social",
                        "shopping",
                        "tech",
                        "music",
                        "crypto",
                        "finance",
                        "news",
                        "blog",
                        "coding",
                        "dating",
                        "photo",
                        "forum",
                        "video",
                        "gaming"
                    ],
                    "exportFormats": ["json"],
                    "extractData": True,
                    "printErrors": False,
                    "recursiveSearch": False,
                    "reportSorting": "default"
                }
            }
        ]
    }

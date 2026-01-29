"""Client for communicating with ingestion service."""

import httpx
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..models import JobStatus, SourceType
from ..config import settings


class IngestionClient:
    """
    Client for interacting with the ingestion service via HTTP.
    """
    
    def __init__(self):
        self.base_url = settings.ingestion_service_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def create_job(
        self,
        source_type: str,
        parameters: dict,
        case_id: Optional[UUID] = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """Create a new ingestion job via HTTP."""
        payload = {
            "source_type": source_type,
            "parameters": parameters,
            "metadata": metadata or {}
        }
        if case_id:
            payload["case_id"] = str(case_id)
        
        response = await self.client.post(f"{self.base_url}/jobs", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_job(self, job_id: UUID) -> Dict[str, Any]:
        """Get job by ID via HTTP."""
        response = await self.client.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        case_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List jobs with filters via HTTP."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if source_type:
            params["source_type"] = source_type
        if case_id:
            params["case_id"] = str(case_id)
        
        response = await self.client.get(f"{self.base_url}/jobs", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_job_stats(self, job_id: UUID) -> Dict[str, Any]:
        """Get job statistics via HTTP."""
        response = await self.client.get(f"{self.base_url}/jobs/{job_id}/stats")
        response.raise_for_status()
        return response.json()

    async def list_evidence(
        self,
        job_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List evidence documents for a job."""
        params = {"job_id": str(job_id), "limit": limit, "offset": offset}
        response = await self.client.get(f"{self.base_url}/evidence", params=params)
        response.raise_for_status()
        return response.json()

    async def get_evidence(self, evidence_id: UUID) -> Dict[str, Any]:
        """Get evidence metadata by ID."""
        response = await self.client.get(f"{self.base_url}/evidence/{evidence_id}")
        response.raise_for_status()
        return response.json()

    async def get_evidence_content(self, evidence_id: UUID) -> Dict[str, Any]:
        """Get evidence content by ID."""
        response = await self.client.get(f"{self.base_url}/evidence/{evidence_id}/content")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

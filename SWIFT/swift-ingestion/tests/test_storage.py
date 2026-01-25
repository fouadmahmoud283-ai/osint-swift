"""Tests for storage layer."""

import pytest
from uuid import uuid4

from src.models import EvidenceDocument, EvidenceType, IngestionJob, JobStatus, SourceType
from src.storage import EvidenceRepository, JobRepository


class TestJobRepository:
    """Tests for JobRepository."""
    
    def test_create_job(self, db_session):
        """Test creating a job."""
        job = IngestionJob(
            source_type=SourceType.OPENCORPORATES,
            parameters={"company_name": "Test Corp"},
            metadata={"test": "data"}
        )
        
        db_job = JobRepository.create_job(db_session, job)
        
        assert db_job.id == job.id
        assert db_job.source_type == SourceType.OPENCORPORATES
        assert db_job.status == JobStatus.PENDING
    
    def test_get_job(self, db_session):
        """Test retrieving a job."""
        job = IngestionJob(source_type=SourceType.OPENCORPORATES)
        JobRepository.create_job(db_session, job)
        
        retrieved = JobRepository.get_job(db_session, job.id)
        
        assert retrieved is not None
        assert retrieved.id == job.id
    
    def test_update_job_status(self, db_session):
        """Test updating job status."""
        job = IngestionJob(source_type=SourceType.OPENCORPORATES)
        JobRepository.create_job(db_session, job)
        
        JobRepository.update_job_status(db_session, job.id, JobStatus.RUNNING)
        
        updated = JobRepository.get_job(db_session, job.id)
        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None


class TestEvidenceRepository:
    """Tests for EvidenceRepository."""
    
    def test_create_evidence(self, db_session):
        """Test creating evidence."""
        job_id = uuid4()
        
        evidence = EvidenceDocument(
            job_id=job_id,
            source_type=SourceType.OPENCORPORATES,
            object_key="test/key",
            checksum="abc123",
            file_size_bytes=1024,
            evidence_type=EvidenceType.COMPANY_RECORD
        )
        
        db_evidence = EvidenceRepository.create_evidence(db_session, evidence)
        
        assert db_evidence.id == evidence.id
        assert db_evidence.job_id == job_id
        assert db_evidence.checksum == "abc123"
    
    def test_get_evidence_by_checksum(self, db_session):
        """Test finding evidence by checksum (deduplication)."""
        evidence = EvidenceDocument(
            job_id=uuid4(),
            source_type=SourceType.OPENCORPORATES,
            object_key="test/key",
            checksum="unique123",
            file_size_bytes=1024,
            evidence_type=EvidenceType.COMPANY_RECORD
        )
        
        EvidenceRepository.create_evidence(db_session, evidence)
        
        found = EvidenceRepository.get_evidence_by_checksum(db_session, "unique123")
        
        assert found is not None
        assert found.id == evidence.id

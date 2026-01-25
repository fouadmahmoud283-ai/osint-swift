# SWIFT Ingestion Service

**Sprint 1 Implementation** - Data Ingestion & Evidence Backbone

## Overview

The SWIFT Ingestion Service is responsible for collecting raw data from external sources, storing it securely with full traceability, and preparing it for downstream processing by the Core AI Engine.

This is a **Sprint 1** implementation focusing on:
- ✅ Robust data ingestion from multiple sources
- ✅ Evidence storage with chain of custody
- ✅ Asynchronous job processing
- ✅ Complete audit trail and traceability
- ✅ Failure handling and recovery

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  SWIFT Ingestion Service                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │  Connectors  │──────│   Registry   │               │
│  └──────────────┘      └──────────────┘               │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Service    │──────│    Worker    │               │
│  │  (Ingestion) │      │   (Celery)   │               │
│  └──────────────┘      └──────────────┘               │
│         │                      │                       │
│         ▼                      ▼                       │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Storage    │      │   Database   │               │
│  │  (S3/MinIO)  │      │  (Postgres)  │               │
│  └──────────────┘      └──────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## Features

### 🔌 Connector Framework
- **Base Connector Interface**: Extensible framework for adding new data sources
- **OpenCorporates Connector**: Production-ready implementation for company data
- **Connector Registry**: Dynamic connector management and discovery
- **Rate Limiting & Retries**: Built-in resilience and API compliance

### 💾 Evidence Storage
- **Object Storage**: S3-compatible storage (MinIO) for raw documents
- **Metadata Database**: PostgreSQL for searchable metadata and relationships
- **Checksum Verification**: SHA-256 hashing for integrity validation
- **Deduplication**: Automatic detection of duplicate evidence

### ⚙️ Job Processing
- **Asynchronous Execution**: Celery + Redis for scalable background processing
- **Status Tracking**: Real-time job status and progress monitoring
- **Failure Recovery**: Automatic retries and partial success handling
- **Statistics**: Detailed metrics for each ingestion job

### 📊 Observability
- **Structured Logging**: JSON logs for production, colored output for development
- **Audit Trail**: Complete chain of custody for all evidence
- **Health Checks**: Service and connector health monitoring

## Data Models

### Ingestion Job
Tracks the execution of a data collection task.

```python
{
    "id": "uuid",
    "source_type": "opencorporates",
    "status": "success",
    "parameters": {"company_name": "Example Corp"},
    "total_items": 10,
    "successful_items": 10,
    "failed_items": 0,
    "created_at": "2025-01-23T10:00:00Z",
    "completed_at": "2025-01-23T10:01:30Z"
}
```

### Evidence Document
Represents a single piece of stored evidence.

```python
{
    "id": "uuid",
    "job_id": "uuid",
    "source_type": "opencorporates",
    "source_url": "https://opencorporates.com/...",
    "object_key": "evidence/opencorporates/2025/01/23/...",
    "checksum": "sha256_hash",
    "file_size_bytes": 4096,
    "evidence_type": "company_record",
    "ingested_at": "2025-01-23T10:00:00Z"
}
```

## Available Connectors

### OpenCorporates
Fetches company registration data, officers, and filings.

**Configuration:**
```python
{
    "api_key": "your_api_key",
    "rate_limit_per_minute": 60,
    "timeout_seconds": 30
}
```

**Parameters:**
```python
{
    "company_name": "Example Corp",          # Required
    "jurisdiction_code": "us_de",            # Optional
    "include_inactive": False                # Optional
}
```

### News API ✨ NEW - FREE!
Fetches news articles from 80,000+ sources worldwide.

**Free Tier:** 1000 requests/day

**Configuration:**
```python
{
    "api_key": "your_api_key",               # Get free at newsapi.org
    "rate_limit_per_minute": 6,
    "timeout_seconds": 30
}
```

**Parameters:**
```python
{
    "query": "Tesla OR Elon Musk",           # Required
    "from_date": "2024-01-01",               # Optional (YYYY-MM-DD)
    "to_date": "2024-01-31",                 # Optional (YYYY-MM-DD)
    "language": "en",                        # Optional
    "sort_by": "relevancy",                  # Optional: relevancy, popularity, publishedAt
    "domains": "reuters.com,bbc.co.uk",      # Optional
    "max_articles": 50                       # Optional (default: 100)
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "Tesla OR SpaceX",
      "from_date": "2024-01-01",
      "language": "en"
    }
  }'
```

**[📖 Full News API Guide](./docs/NEWS_API_GUIDE.md)**

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- MinIO or S3

### Local Development

1. **Install Dependencies**
```bash
cd swift-ingestion
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Initialize Database**
```bash
python scripts/init_db.py
```

4. **Start Worker**
```bash
celery -A src.services.worker worker --loglevel=info
```

### Docker Deployment

```bash
# From SWIFT root directory
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Ingestion Worker

## Usage Examples

### Python SDK
```python
from src.services import IngestionService
from src.models import IngestionJobCreate, SourceType

service = IngestionService()

# Create ingestion job
job_create = IngestionJobCreate(
    source_type=SourceType.OPENCORPORATES,
    parameters={
        "company_name": "Tesla Inc",
        "jurisdiction_code": "us_de"
    }
)

job = service.create_job(job_create)

# Execute job (async)
await service.execute_job(job.id)

# Check status
job_status = service.get_job(job.id)
print(f"Status: {job_status.status}")
print(f"Items collected: {job_status.successful_items}")
```

### Via API
```bash
# Create job
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {"company_name": "Tesla Inc"}
  }'

# Check job status
curl http://localhost:8000/ingestion/jobs/{job_id}

# Get statistics
curl http://localhost:8000/ingestion/jobs/{job_id}/stats
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_storage.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://swift:swift123@localhost:5432/swift_db` |
| `S3_ENDPOINT_URL` | S3/MinIO endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET_NAME` | Evidence bucket name | `swift-evidence` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `OPENCORPORATES_API_KEY` | OpenCorporates API key | (required) |
| `LOG_LEVEL` | Logging level | `INFO` |

## Project Structure

```
swift-ingestion/
├── src/
│   ├── connectors/          # Data source connectors
│   │   ├── base.py         # Base connector interface
│   │   ├── opencorporates.py
│   │   └── registry.py     # Connector registry
│   ├── db/                  # Database models
│   │   ├── models.py       # SQLAlchemy models
│   │   └── __init__.py     # Session management
│   ├── services/            # Business logic
│   │   ├── ingestion.py    # Ingestion service
│   │   └── worker.py       # Celery worker
│   ├── storage/             # Storage layer
│   │   ├── object_store.py # S3/MinIO adapter
│   │   └── repository.py   # Database repositories
│   ├── utils/              # Utilities
│   │   └── logging.py      # Structured logging
│   ├── config.py           # Configuration
│   └── models.py           # Pydantic models
├── tests/                  # Unit tests
├── scripts/                # Utility scripts
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Sprint 1 Deliverables ✅

- [x] Connector interface and registry
- [x] OpenCorporates connector implementation
- [x] Object storage adapter (S3/MinIO)
- [x] PostgreSQL metadata storage
- [x] Evidence checksum and integrity validation
- [x] Celery-based job scheduler
- [x] Failure handling and partial success
- [x] Structured logging and audit trail
- [x] Complete traceability (source → storage)
- [x] Docker deployment configuration

## Next Steps (Sprint 2+)

- [ ] Additional connectors (News API, RSS, Web Scraper)
- [ ] NER and entity extraction pipeline
- [ ] Integration with Core AI Engine
- [ ] Advanced deduplication logic
- [ ] Evidence retention policies
- [ ] Performance monitoring dashboard
- [ ] API authentication and authorization

## License

Proprietary - SWIFT Intelligence Platform

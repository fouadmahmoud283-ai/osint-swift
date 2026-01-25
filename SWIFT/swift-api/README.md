# SWIFT API Gateway

**Sprint 1 Implementation** - FastAPI Gateway for Ingestion Management

## Overview

The SWIFT API Gateway provides HTTP endpoints for managing the SWIFT Intelligence Platform. In Sprint 1, it focuses on ingestion job management and monitoring.

## Features

- ✅ RESTful API for ingestion job management
- ✅ Real-time job status monitoring
- ✅ Job statistics and metrics
- ✅ Auto-generated API documentation (OpenAPI/Swagger)
- ✅ CORS support for web clients
- ✅ Structured error handling

## API Endpoints

### Health & Info
- `GET /` - Root endpoint with API info
- `GET /health` - Health check

### Ingestion Management
- `POST /ingestion/jobs` - Create a new ingestion job
- `GET /ingestion/jobs` - List all ingestion jobs (with filters)
- `GET /ingestion/jobs/{job_id}` - Get job details
- `GET /ingestion/jobs/{job_id}/stats` - Get job statistics
- `GET /ingestion/sources` - List available data sources

## Quick Start

### Local Development

```bash
cd swift-api
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://swift:swift123@localhost:5432/swift_db
export CELERY_BROKER_URL=redis://localhost:6379/0

# Run server
uvicorn src.main:app --reload --port 8000
```

### Docker

```bash
docker-compose up swift-api
```

### Access API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Usage Examples

### Create Ingestion Job

```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {
      "company_name": "Tesla Inc",
      "jurisdiction_code": "us_de"
    },
    "metadata": {
      "analyst": "john.doe",
      "priority": "high"
    }
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_type": "opencorporates",
  "status": "pending",
  "parameters": {
    "company_name": "Tesla Inc",
    "jurisdiction_code": "us_de"
  },
  "created_at": "2025-01-23T10:00:00Z",
  "total_items": 0,
  "successful_items": 0,
  "failed_items": 0,
  "celery_task_id": "task_id_here"
}
```

### List Jobs

```bash
# All jobs
curl http://localhost:8000/ingestion/jobs

# Filter by status
curl http://localhost:8000/ingestion/jobs?status=success

# Filter by source
curl http://localhost:8000/ingestion/jobs?source_type=opencorporates

# Pagination
curl http://localhost:8000/ingestion/jobs?limit=10&offset=20
```

### Get Job Status

```bash
curl http://localhost:8000/ingestion/jobs/550e8400-e29b-41d4-a716-446655440000
```

### Get Job Statistics

```bash
curl http://localhost:8000/ingestion/jobs/550e8400-e29b-41d4-a716-446655440000/stats
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "duration_seconds": 45.2,
  "total_items": 10,
  "successful_items": 10,
  "failed_items": 0,
  "avg_item_size_bytes": 4096,
  "total_size_bytes": 40960
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API host address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://swift:swift123@localhost:5432/swift_db` |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/0` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["http://localhost:3000"]` |
| `ENVIRONMENT` | Environment name | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Project Structure

```
swift-api/
├── src/
│   ├── routes/
│   │   ├── __init__.py
│   │   └── ingestion.py    # Ingestion endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── ingestion_client.py  # Ingestion service client
│   ├── config.py           # Configuration
│   └── main.py             # FastAPI application
├── requirements.txt
├── Dockerfile
└── README.md
```

## Dependencies

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **SQLAlchemy**: Database ORM
- **Celery**: Task queue client

## Error Handling

The API returns standard HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include details:
```json
{
  "detail": "Invalid source type: invalid_source"
}
```

## Next Steps (Sprint 2+)

- [ ] Authentication and authorization
- [ ] API rate limiting
- [ ] WebSocket support for real-time updates
- [ ] Case management endpoints
- [ ] Evidence retrieval endpoints
- [ ] User management
- [ ] API versioning

## License

Proprietary - SWIFT Intelligence Platform

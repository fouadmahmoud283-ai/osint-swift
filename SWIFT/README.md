# SWIFT Intelligence Platform

**Sprint 1 Complete** - Data Ingestion & Evidence Backbone

## 🎯 Project Vision

SWIFT is a core-centric AI investigation platform where a central intelligence engine builds and reasons over a knowledge graph. All modules (Due Diligence, Investigations, Media Analysis) are controlled ways of asking that engine questions and generating outputs.

**Mental Model**: SWIFT is one brain (Core Engine) with multiple arms (modules). The brain owns data, logic, memory, and reasoning. Modules are interfaces and workflows, not intelligence.

## 📦 Sprint 1 Implementation

Sprint 1 delivers a **production-ready data ingestion and evidence storage system** with:

### ✅ Completed Features

1. **Ingestion Service** (`swift-ingestion`)
   - Extensible connector framework
   - OpenCorporates connector (company data)
   - Asynchronous job processing (Celery)
   - S3-compatible evidence storage
   - PostgreSQL metadata storage
   - SHA-256 checksum verification
   - Complete audit trail

2. **API Gateway** (`swift-api`)
   - RESTful API for job management
   - Real-time status monitoring
   - Job statistics and metrics
   - Auto-generated documentation
   - CORS support

3. **Infrastructure**
   - Docker Compose orchestration
   - PostgreSQL database
   - Redis message broker
   - MinIO object storage
   - Structured logging
   - Health checks

### 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      SWIFT Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐        ┌──────────────┐                 │
│  │  swift-api   │────────│ swift-core   │  (Sprint 2+)    │
│  │  (Gateway)   │        │ (AI Engine)  │                 │
│  └──────────────┘        └──────────────┘                 │
│         │                        │                         │
│         │                        │                         │
│         ▼                        ▼                         │
│  ┌──────────────────────────────────────┐                 │
│  │      swift-ingestion (Sprint 1)      │                 │
│  ├──────────────────────────────────────┤                 │
│  │ • Connectors (OpenCorporates, ...)   │                 │
│  │ • Evidence Storage (S3/MinIO)        │                 │
│  │ • Job Processing (Celery)            │                 │
│  │ • Audit Trail & Traceability         │                 │
│  └──────────────────────────────────────┘                 │
│         │              │              │                    │
│         ▼              ▼              ▼                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Postgres │  │  Redis   │  │  MinIO   │               │
│  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- OpenCorporates API key ([Get one here](https://opencorporates.com/api_accounts/new))

### 1. Clone & Configure

```bash
cd e:\Syntera_AI\portofilio-projects\osint\SWIFT

# Configure environment
cp .env.example .env
# Edit .env and add your OPENCORPORATES_API_KEY
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** (port 5432) - Metadata storage
- **Redis** (port 6379) - Job queue
- **MinIO** (ports 9000, 9001) - Object storage
- **SWIFT API** (port 8000) - HTTP API
- **Ingestion Worker** - Background processing

### 3. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Check MinIO console
open http://localhost:9001
# Login: minioadmin / minioadmin
```

### 4. Initialize Database

```bash
docker exec swift-ingestion-worker python scripts/init_db.py
```

### 5. Run Your First Ingestion

```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {
      "company_name": "Tesla Inc",
      "jurisdiction_code": "us_de"
    }
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "celery_task_id": "...",
  ...
}
```

### 6. Check Job Status

```bash
# Get job details
curl http://localhost:8000/ingestion/jobs/550e8400-e29b-41d4-a716-446655440000

# Get statistics
curl http://localhost:8000/ingestion/jobs/550e8400-e29b-41d4-a716-446655440000/stats
```

### 7. View API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Repository Structure

```
SWIFT/
├── swift-api/              # FastAPI Gateway (Sprint 1)
│   ├── src/
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Service clients
│   │   └── main.py        # FastAPI app
│   ├── Dockerfile
│   └── README.md
│
├── swift-ingestion/        # Ingestion Service (Sprint 1 ✅)
│   ├── src/
│   │   ├── connectors/    # Data source connectors
│   │   ├── services/      # Business logic
│   │   ├── storage/       # Storage layer
│   │   └── db/            # Database models
│   ├── tests/             # Unit tests
│   ├── scripts/           # Utility scripts
│   ├── Dockerfile
│   └── README.md
│
├── swift-core/             # Core AI Engine (Sprint 2+)
│   └── README.md
│
├── swift-modules/          # Investigation Modules (Sprint 3+)
│   └── README.md
│
├── docker-compose.yml      # Service orchestration
├── .env                    # Environment config
└── README.md              # This file
```

## 🔌 Available Data Sources

### OpenCorporates
Company registration data from 140+ jurisdictions worldwide.

**Example:**
```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {
      "company_name": "Apple Inc",
      "jurisdiction_code": "us_ca"
    }
  }'
```

### News API ✨ NEW - FREE!
News articles from 80,000+ sources. **Free tier: 1000 requests/day**

Get your free API key: https://newsapi.org/register

**Example:**
```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "Tesla OR Elon Musk",
      "from_date": "2024-01-01",
      "language": "en",
      "max_articles": 50
    }
  }'
```

**[📖 Full News API Guide](./swift-ingestion/docs/NEWS_API_GUIDE.md)**

### Coming Soon
- RSS Feeds (Free)
- Web Scraper (Free)
- PIPL (Identity & Contact Data)
- Custom CSV/JSON uploads

## 🧪 Testing

```bash
# Run ingestion tests
cd swift-ingestion
pytest

# With coverage
pytest --cov=src --cov-report=html
```

## 📊 Monitoring & Logs

### View Logs

```bash
# API logs
docker logs swift-api -f

# Worker logs
docker logs swift-ingestion-worker -f

# All services
docker-compose logs -f
```

### MinIO Console

Access at http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

Browse stored evidence in the `swift-evidence` bucket.

## 🔧 Development

### Local Development (without Docker)

1. **Start Infrastructure**
```bash
docker-compose up postgres redis minio -d
```

2. **Install Dependencies**
```bash
# API
cd swift-api
pip install -r requirements.txt

# Ingestion
cd swift-ingestion
pip install -r requirements.txt
```

3. **Run Services**
```bash
# Terminal 1: API
cd swift-api
uvicorn src.main:app --reload

# Terminal 2: Worker
cd swift-ingestion
celery -A src.services.worker worker --loglevel=info
```

## 📋 Sprint Roadmap

### ✅ Sprint 1 (Weeks 1-2) - COMPLETE
- [x] Ingestion service architecture
- [x] OpenCorporates connector
- [x] Evidence storage (S3 + Postgres)
- [x] Job processing (Celery)
- [x] API endpoints
- [x] Logging & traceability
- [x] Docker deployment

### 🔜 Sprint 2 (Weeks 3-4)
- [ ] Entity extraction (NER)
- [ ] Core AI engine skeleton
- [ ] Entity resolution
- [ ] Knowledge graph builder
- [ ] Basic retrieval layer

### 🔜 Sprint 3 (Weeks 5-6)
- [ ] Scoring & flag engine
- [ ] LLM integration
- [ ] Evidence binder
- [ ] ADD module (v1)

## 📖 Documentation

- [Project Proposal](./Project_porposal.md) - Full system design
- [Sprint 1 Plan](./sprint1.md) - Sprint 1 scope and deliverables
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Ingestion Service](./swift-ingestion/README.md) - Ingestion details
- [API Gateway](./swift-api/README.md) - API details

## 🤝 Contributing

This is a portfolio project demonstrating professional software architecture and development practices.

## 📄 License

Proprietary - SWIFT Intelligence Platform

## 🎯 Sprint 1 Success Criteria - ALL MET ✅

- [x] At least one external data source ingested (OpenCorporates)
- [x] Raw data safely stored with integrity checks (SHA-256)
- [x] Evidence traceable back to source (complete audit trail)
- [x] System survives failures (retries, partial success handling)
- [x] Professional architecture and clean code
- [x] Comprehensive documentation
- [x] Docker deployment ready
- [x] Unit tests implemented

---

**Built with**: Python 3.11 | FastAPI | PostgreSQL | Redis | Celery | MinIO | Docker

# SWIFT Sprint 1 - Verification Checklist

Use this checklist to verify the Sprint 1 implementation is working correctly.

## ✅ Pre-Flight Checks

- [ ] Docker Desktop is installed and running
- [ ] Python 3.11+ is installed (for local dev)
- [ ] You have an OpenCorporates API key
- [ ] Ports 5432, 6379, 8000, 9000, 9001 are available

## ✅ Setup Verification

### 1. Environment Configuration
```powershell
# Check .env file exists
Test-Path .env

# Verify API key is set
Select-String -Path .env -Pattern "OPENCORPORATES_API_KEY"
```

### 2. Docker Services
```powershell
# Start all services
docker-compose up -d

# Verify all containers are running
docker-compose ps

# Expected output:
# swift-postgres          running
# swift-redis            running
# swift-minio            running
# swift-api              running
# swift-ingestion-worker running
```

### 3. Service Health Checks
```powershell
# PostgreSQL
docker exec swift-postgres pg_isready -U swift
# Expected: localhost:5432 - accepting connections

# Redis
docker exec swift-redis redis-cli ping
# Expected: PONG

# MinIO
Invoke-WebRequest -Uri http://localhost:9000/minio/health/live
# Expected: StatusCode 200

# API
Invoke-WebRequest -Uri http://localhost:8000/health | ConvertFrom-Json
# Expected: {"status":"healthy","service":"swift-api","version":"0.1.0"}
```

### 4. Database Initialization
```powershell
# Initialize database schema
docker exec swift-ingestion-worker python scripts/init_db.py

# Check logs for success
docker logs swift-ingestion-worker --tail 50
# Expected: "Database initialized successfully"
```

## ✅ Functional Tests

### 1. Create Ingestion Job
```powershell
$body = @{
    source_type = "opencorporates"
    parameters = @{
        company_name = "Tesla Inc"
    }
} | ConvertTo-Json

$response = Invoke-WebRequest -Method POST `
    -Uri http://localhost:8000/ingestion/jobs `
    -ContentType "application/json" `
    -Body $body | ConvertFrom-Json

$jobId = $response.id
Write-Host "Job ID: $jobId"
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "source_type": "opencorporates",
  "status": "pending",
  "total_items": 0,
  "successful_items": 0,
  "failed_items": 0,
  "celery_task_id": "task-id-here"
}
```

### 2. Monitor Job Progress
```powershell
# Wait a few seconds for job to execute
Start-Sleep -Seconds 10

# Check job status
Invoke-WebRequest -Uri "http://localhost:8000/ingestion/jobs/$jobId" | ConvertFrom-Json
```

**Expected Response (after completion):**
```json
{
  "status": "success",
  "total_items": 10,
  "successful_items": 10,
  "failed_items": 0,
  "completed_at": "2025-01-23T..."
}
```

### 3. Get Job Statistics
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/ingestion/jobs/$jobId/stats" | ConvertFrom-Json
```

**Expected Response:**
```json
{
  "job_id": "uuid-here",
  "status": "success",
  "duration_seconds": 45.2,
  "total_items": 10,
  "avg_item_size_bytes": 4096,
  "total_size_bytes": 40960
}
```

### 4. List All Jobs
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/ingestion/jobs" | ConvertFrom-Json
```

### 5. Filter Jobs
```powershell
# By status
Invoke-WebRequest -Uri "http://localhost:8000/ingestion/jobs?status=success" | ConvertFrom-Json

# By source type
Invoke-WebRequest -Uri "http://localhost:8000/ingestion/jobs?source_type=opencorporates" | ConvertFrom-Json
```

## ✅ Storage Verification

### 1. Check PostgreSQL Data
```powershell
docker exec swift-postgres psql -U swift -d swift_db -c "SELECT COUNT(*) FROM ingestion_jobs;"
docker exec swift-postgres psql -U swift -d swift_db -c "SELECT COUNT(*) FROM evidence_documents;"
```

### 2. Check MinIO Object Storage
1. Open http://localhost:9001
2. Login with: `minioadmin` / `minioadmin`
3. Navigate to `swift-evidence` bucket
4. Verify evidence files are present
5. Download a file and verify it's valid JSON

### 3. Check Redis Queue
```powershell
docker exec swift-redis redis-cli keys "*"
# Should show Celery task keys
```

## ✅ API Documentation

### 1. Swagger UI
- [ ] Open http://localhost:8000/docs
- [ ] Verify all endpoints are listed
- [ ] Try "Try it out" on GET /health
- [ ] Verify interactive docs work

### 2. ReDoc
- [ ] Open http://localhost:8000/redoc
- [ ] Verify documentation is readable
- [ ] Check all endpoints are documented

## ✅ Logging & Monitoring

### 1. Check Logs
```powershell
# API logs
docker logs swift-api --tail 50

# Worker logs
docker logs swift-ingestion-worker --tail 50

# All services
docker-compose logs --tail 100
```

**Expected Log Format:**
```json
{
  "event": "Created ingestion job ...",
  "timestamp": "2025-01-23T...",
  "level": "INFO",
  "job_id": "...",
  "source_type": "opencorporates"
}
```

### 2. Error Handling
```powershell
# Try invalid source type
$badBody = @{
    source_type = "invalid_source"
    parameters = @{}
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
    -Uri http://localhost:8000/ingestion/jobs `
    -ContentType "application/json" `
    -Body $badBody
# Expected: HTTP 400 Bad Request
```

## ✅ Performance & Resilience

### 1. Concurrent Jobs
```powershell
# Submit 5 jobs simultaneously
1..5 | ForEach-Object {
    $body = @{
        source_type = "opencorporates"
        parameters = @{ company_name = "Company $_" }
    } | ConvertTo-Json
    
    Invoke-WebRequest -Method POST `
        -Uri http://localhost:8000/ingestion/jobs `
        -ContentType "application/json" `
        -Body $body -UseBasicParsing
}

# All should be queued successfully
```

### 2. Service Recovery
```powershell
# Stop worker
docker stop swift-ingestion-worker

# Submit a job (should still be accepted)
# ...

# Restart worker
docker start swift-ingestion-worker

# Job should be processed after restart
```

## ✅ Code Quality

### 1. Run Tests
```powershell
cd swift-ingestion
python -m pytest -v
```

**Expected:**
- All tests pass
- No errors or warnings

### 2. Type Checking (Optional)
```powershell
cd swift-ingestion
mypy src/
```

### 3. Linting (Optional)
```powershell
cd swift-ingestion
ruff check src/
```

## ✅ Documentation

- [ ] README.md is complete and accurate
- [ ] QUICKSTART.md provides 5-minute setup
- [ ] SPRINT1_SUMMARY.md documents implementation
- [ ] API documentation is auto-generated
- [ ] All code has docstrings
- [ ] setup.ps1 script works

## 🎯 Final Verification

Run the complete test scenario:

```powershell
# 1. Clean start
docker-compose down -v
docker-compose up -d

# 2. Initialize
docker exec swift-ingestion-worker python scripts/init_db.py

# 3. Create job
$response = Invoke-WebRequest -Method POST `
    -Uri http://localhost:8000/ingestion/jobs `
    -ContentType "application/json" `
    -Body '{"source_type":"opencorporates","parameters":{"company_name":"Tesla"}}' `
    | ConvertFrom-Json

# 4. Wait and verify
Start-Sleep -Seconds 15
$final = Invoke-WebRequest -Uri "http://localhost:8000/ingestion/jobs/$($response.id)" `
    | ConvertFrom-Json

# 5. Check success
$final.status -eq "success" -and $final.successful_items -gt 0
```

**Expected:** `True`

## 📊 Success Criteria

All items below should be checked:

- [ ] All Docker containers running
- [ ] API responds to health checks
- [ ] Database is initialized
- [ ] Can create ingestion jobs
- [ ] Jobs execute successfully
- [ ] Evidence is stored in MinIO
- [ ] Metadata is in PostgreSQL
- [ ] Logs are structured and informative
- [ ] API documentation is accessible
- [ ] Tests pass
- [ ] No errors in logs during normal operation

## 🎉 Sprint 1 Complete!

If all checks pass, Sprint 1 is successfully implemented and verified.

---

**Note:** Some checks may vary based on API key limits or network conditions. The core functionality should work consistently.

# SWIFT Platform Setup Script (PowerShell)
# Sprint 1 - Data Ingestion & Evidence Backbone

$ErrorActionPreference = "Stop"

Write-Host "🚀 SWIFT Platform - Sprint 1 Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "📝 Please edit .env and add your OPENCORPORATES_API_KEY" -ForegroundColor Yellow
    Write-Host "   Get one from: https://opencorporates.com/api_accounts/new" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter after you've added your API key"
}

Write-Host "✅ Environment configuration found" -ForegroundColor Green

# Stop any existing containers
Write-Host ""
Write-Host "🧹 Cleaning up any existing containers..." -ForegroundColor Cyan
docker-compose down 2>$null

# Start services
Write-Host ""
Write-Host "🐳 Starting SWIFT services..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Cyan
Write-Host "   This may take 30-60 seconds..." -ForegroundColor Cyan

# Wait for PostgreSQL
Write-Host -NoNewline "   Waiting for PostgreSQL..."
for ($i = 1; $i -le 30; $i++) {
    try {
        docker exec swift-postgres pg_isready -U swift 2>$null | Out-Null
        Write-Host " ✅" -ForegroundColor Green
        break
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
}

# Wait for Redis
Write-Host -NoNewline "   Waiting for Redis..."
for ($i = 1; $i -le 30; $i++) {
    try {
        docker exec swift-redis redis-cli ping 2>$null | Out-Null
        Write-Host " ✅" -ForegroundColor Green
        break
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
}

# Wait for MinIO
Write-Host -NoNewline "   Waiting for MinIO..."
for ($i = 1; $i -le 30; $i++) {
    try {
        Invoke-WebRequest -Uri http://localhost:9000/minio/health/live -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host " ✅" -ForegroundColor Green
        break
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
}

# Wait for API
Write-Host -NoNewline "   Waiting for API..."
for ($i = 1; $i -le 30; $i++) {
    try {
        Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host " ✅" -ForegroundColor Green
        break
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }
}

# Initialize database
Write-Host ""
Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
docker exec swift-ingestion-worker python scripts/init_db.py

Write-Host ""
Write-Host "✅ SWIFT Platform is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   • API Documentation: http://localhost:8000/docs"
Write-Host "   • MinIO Console:     http://localhost:9001 (minioadmin/minioadmin)"
Write-Host "   • API Health:        http://localhost:8000/health"
Write-Host ""
Write-Host "🧪 Test the system:" -ForegroundColor Cyan
Write-Host '   Invoke-WebRequest -Method POST -Uri http://localhost:8000/ingestion/jobs \'
Write-Host '     -ContentType "application/json" \'
Write-Host '     -Body ''{"source_type": "opencorporates", "parameters": {"company_name": "Tesla"}}'''
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • README.md - Full documentation"
Write-Host "   • QUICKSTART.md - Quick start guide"
Write-Host "   • SPRINT1_SUMMARY.md - Implementation summary"
Write-Host ""
Write-Host "🎉 Happy investigating!" -ForegroundColor Green

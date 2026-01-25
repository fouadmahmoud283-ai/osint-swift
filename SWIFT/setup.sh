#!/bin/bash

# SWIFT Platform Setup Script
# Sprint 1 - Data Ingestion & Evidence Backbone

set -e  # Exit on error

echo "🚀 SWIFT Platform - Sprint 1 Setup"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OPENCORPORATES_API_KEY"
    echo "   Get one from: https://opencorporates.com/api_accounts/new"
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

echo "✅ Environment configuration found"

# Stop any existing containers
echo ""
echo "🧹 Cleaning up any existing containers..."
docker-compose down 2>/dev/null || true

# Start services
echo ""
echo "🐳 Starting SWIFT services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo "   This may take 30-60 seconds..."

# Wait for PostgreSQL
echo -n "   Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec swift-postgres pg_isready -U swift > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Redis
echo -n "   Waiting for Redis..."
for i in {1..30}; do
    if docker exec swift-redis redis-cli ping > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for MinIO
echo -n "   Waiting for MinIO..."
for i in {1..30}; do
    if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for API
echo -n "   Waiting for API..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 2
done

# Initialize database
echo ""
echo "🗄️  Initializing database..."
docker exec swift-ingestion-worker python scripts/init_db.py

echo ""
echo "✅ SWIFT Platform is ready!"
echo ""
echo "📍 Access Points:"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • MinIO Console:     http://localhost:9001 (minioadmin/minioadmin)"
echo "   • API Health:        http://localhost:8000/health"
echo ""
echo "🧪 Test the system:"
echo '   curl -X POST http://localhost:8000/ingestion/jobs \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"source_type": "opencorporates", "parameters": {"company_name": "Tesla"}}'"'"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Full documentation"
echo "   • QUICKSTART.md - Quick start guide"
echo "   • SPRINT1_SUMMARY.md - Implementation summary"
echo ""
echo "🎉 Happy investigating!"

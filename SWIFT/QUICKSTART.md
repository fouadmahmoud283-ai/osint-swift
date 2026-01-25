# SWIFT - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Get an API Key

Sign up for a free OpenCorporates API key:
👉 https://opencorporates.com/api_accounts/new

### Step 2: Configure

```bash
cd e:\Syntera_AI\portofilio-projects\osint\SWIFT

# Create .env file
echo OPENCORPORATES_API_KEY=your_key_here > .env
```

### Step 3: Start SWIFT

```bash
docker-compose up -d
```

Wait ~30 seconds for services to start.

### Step 4: Initialize Database

```bash
docker exec swift-ingestion-worker python scripts/init_db.py
```

### Step 5: Test It!

```bash
# Create an ingestion job
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {"company_name": "Tesla"}
  }'
```

You'll get back a job ID. Check its status:

```bash
curl http://localhost:8000/ingestion/jobs/{job_id}
```

### Step 6: Explore

- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Logs**: `docker-compose logs -f`

## 🎯 What Just Happened?

1. ✅ SWIFT fetched company data from OpenCorporates
2. ✅ Stored raw evidence in MinIO (S3-compatible storage)
3. ✅ Saved metadata in PostgreSQL
4. ✅ Generated SHA-256 checksum for integrity
5. ✅ Created complete audit trail

## 🆕 Try the News API (FREE!)

Get a free News API key: https://newsapi.org/register

```bash
# Add to .env
echo NEWS_API_KEY=your_key_here >> .env

# Restart services
docker-compose restart

# Fetch news about a company
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

## 🔍 View Your Evidence

1. Open http://localhost:9001
2. Login: minioadmin / minioadmin
3. Browse `swift-evidence` bucket
4. See your collected evidence files!

## ⚠️ Troubleshooting

**Services not starting?**
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

**Job stuck in pending?**
```bash
# Check worker logs
docker logs swift-ingestion-worker -f
```

**Database connection errors?**
```bash
# Wait for Postgres to be ready
docker exec swift-postgres pg_isready -U swift
```

## 📚 Next Steps

- Read [Main README](./README.md) for full documentation
- Explore [API Documentation](http://localhost:8000/docs)
- Check [Architecture](./Project_porposal.md)

---

**Need Help?** Check the logs: `docker-compose logs -f`

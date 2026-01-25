# SWIFT Data Sources - Comparison Guide

## Available Connectors

SWIFT currently supports 2 production-ready data connectors for OSINT investigations.

## Quick Comparison

| Feature | OpenCorporates | News API |
|---------|---------------|----------|
| **Cost** | Paid (API key required) | ✅ **FREE** (1000/day) |
| **Data Type** | Company records | News articles |
| **Coverage** | 140+ jurisdictions | 80,000+ sources |
| **Best For** | Corporate due diligence | Media monitoring, research |
| **Rate Limit** | Varies by plan | 1000 requests/day (free) |
| **Historical Data** | Full history | Last 30 days (free tier) |
| **Setup Time** | 5 minutes | 2 minutes |

## When to Use Each

### Use OpenCorporates For:
- ✅ Company registration verification
- ✅ Officer and director information
- ✅ Corporate structure analysis
- ✅ Multi-jurisdiction research
- ✅ Historical company data
- ✅ Legal entity identification

**Example Use Cases:**
- Verifying company legitimacy
- Finding company officers
- Corporate network mapping
- Compliance checks
- Background investigations

### Use News API For:
- ✅ Media monitoring
- ✅ Reputation research
- ✅ Event tracking
- ✅ Person mentions
- ✅ Industry analysis
- ✅ Real-time news

**Example Use Cases:**
- Company news monitoring
- Executive background checks
- Controversy detection
- Market intelligence
- Event correlation
- Sentiment analysis

## Cost Analysis

### OpenCorporates
- **Free Tier**: 500 requests/month (limited)
- **Basic**: $9/month - 10,000 credits
- **Pro**: Custom pricing
- **Best For**: Regular corporate research

### News API ⭐ Recommended for Getting Started
- **Free Tier**: 1000 requests/day (FREE!)
- **Developer**: $449/month - unlimited
- **Business**: $999/month - enhanced features
- **Best For**: Learning, prototyping, small projects

## Setup Comparison

### OpenCorporates Setup
```bash
# 1. Sign up at opencorporates.com
# 2. Purchase API plan
# 3. Get API key
# 4. Add to .env
echo OPENCORPORATES_API_KEY=your_key >> .env
```

### News API Setup ⚡ Fastest
```bash
# 1. Sign up at newsapi.org (FREE!)
# 2. Get instant API key
# 3. Add to .env
echo NEWS_API_KEY=your_key >> .env
```

## Example Workflows

### Corporate Due Diligence Workflow
```bash
# Step 1: Get company info from OpenCorporates
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {"company_name": "Acme Corp"}
  }'

# Step 2: Get news about the company
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "\"Acme Corp\" AND (lawsuit OR fraud OR investigation)",
      "from_date": "2023-01-01"
    }
  }'
```

### Person Background Check Workflow
```bash
# Step 1: Get news mentions
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "\"John Smith\" AND (CEO OR executive)",
      "max_articles": 100
    }
  }'

# Step 2: Find their companies (if identified)
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "opencorporates",
    "parameters": {"company_name": "Smith Ventures"}
  }'
```

## Data Quality

### OpenCorporates
- ✅ **Accuracy**: Very high (official records)
- ✅ **Completeness**: Comprehensive
- ✅ **Reliability**: Excellent
- ✅ **Structure**: Highly structured
- ⚠️ **Freshness**: Varies by jurisdiction

### News API
- ✅ **Coverage**: Extensive (80,000 sources)
- ✅ **Freshness**: Real-time
- ✅ **Diversity**: Multiple perspectives
- ⚠️ **Accuracy**: Varies by source
- ⚠️ **Structure**: Semi-structured

## Rate Limiting & Best Practices

### OpenCorporates
```python
# Recommended settings
{
    "rate_limit_per_minute": 60,  # Adjust based on plan
    "timeout_seconds": 30,
    "retry_attempts": 3
}
```

### News API (Free Tier)
```python
# Optimized for free tier
{
    "rate_limit_per_minute": 6,   # Stay under limits
    "timeout_seconds": 30,
    "max_articles": 100            # Limit per request
}
```

## Integration Patterns

### Sequential Investigation
```
1. News API → Identify entities
2. OpenCorporates → Verify companies
3. News API → Deep dive on findings
```

### Parallel Collection
```
OpenCorporates ─┐
                ├─→ Aggregate → Analyze
News API ───────┘
```

### Continuous Monitoring
```
News API (daily) → Alert → OpenCorporates (verify)
```

## Cost Optimization Tips

### For News API (Free Tier)
1. ✅ Use specific queries to reduce results
2. ✅ Set reasonable date ranges
3. ✅ Use `max_articles` parameter
4. ✅ Filter by trusted domains
5. ✅ Batch investigations daily

### For OpenCorporates
1. ✅ Cache results (use our checksums!)
2. ✅ Deduplicate before querying
3. ✅ Use specific jurisdiction codes
4. ✅ Batch company searches
5. ✅ Monitor credit usage

## Recommendation

### For Learning/Prototyping
**Start with News API (FREE!)** ⭐
- Zero cost to start
- 1000 requests/day is generous
- Perfect for testing SWIFT
- Rich, diverse data

### For Production Use
**Combine Both:**
- News API for monitoring & discovery
- OpenCorporates for verification
- Best of both worlds

## Getting Started

### Option 1: News API Only (FREE)
```bash
# Get free API key
open https://newsapi.org/register

# Add to .env
echo NEWS_API_KEY=your_key >> .env

# Start ingesting!
```

### Option 2: Both Sources (Recommended)
```bash
# Get both API keys
# News API: https://newsapi.org/register (FREE)
# OpenCorporates: https://opencorporates.com/api_accounts/new

# Configure both
echo NEWS_API_KEY=your_news_key >> .env
echo OPENCORPORATES_API_KEY=your_oc_key >> .env
```

## Future Connectors (Planned)

- 🔜 RSS Feeds (FREE)
- 🔜 Web Scraper (FREE)
- 🔜 LinkedIn (via scraping)
- 🔜 Companies House UK (FREE)
- 🔜 SEC Edgar (FREE)
- 🔜 Twitter/X API
- 🔜 PIPL (Paid)

## Support & Documentation

- 📖 [News API Guide](./swift-ingestion/docs/NEWS_API_GUIDE.md)
- 📖 [Ingestion README](./swift-ingestion/README.md)
- 🔗 [News API Docs](https://newsapi.org/docs)
- 🔗 [OpenCorporates API Docs](https://api.opencorporates.com/documentation/API-Reference)

---

**Recommendation**: Start with News API (free) to learn SWIFT, then add OpenCorporates for production corporate investigations.

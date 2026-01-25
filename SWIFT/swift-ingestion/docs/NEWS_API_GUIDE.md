# News API Connector - Quick Start Guide

## Get Your Free API Key

1. Visit https://newsapi.org/register
2. Sign up for a free account
3. Get your API key (1000 requests/day)
4. Add it to your `.env` file

## Configuration

Add to `.env`:
```bash
NEWS_API_KEY=your_api_key_here
```

## Usage Examples

### Search for Company News

```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "Tesla OR Elon Musk",
      "from_date": "2024-01-01",
      "language": "en",
      "sort_by": "relevancy",
      "max_articles": 50
    }
  }'
```

### Search News About a Person

```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "\"Sam Altman\" AND (OpenAI OR AI)",
      "from_date": "2023-01-01",
      "language": "en"
    }
  }'
```

### Filter by Specific Domains

```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "cryptocurrency regulation",
      "domains": "reuters.com,bloomberg.com,ft.com",
      "sort_by": "publishedAt"
    }
  }'
```

### Last 7 Days of News

```bash
curl -X POST http://localhost:8000/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "news_api",
    "parameters": {
      "query": "artificial intelligence",
      "from_date": "2024-01-19",
      "to_date": "2024-01-26",
      "language": "en",
      "max_articles": 100
    }
  }'
```

## Parameters Reference

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `query` | string | ✅ Yes | Search query (supports AND, OR, NOT) | `"Tesla OR SpaceX"` |
| `from_date` | string | No | Start date (YYYY-MM-DD) | `"2024-01-01"` |
| `to_date` | string | No | End date (YYYY-MM-DD) | `"2024-01-31"` |
| `language` | string | No | Language code (en, es, fr, de, etc.) | `"en"` |
| `sort_by` | string | No | Sort order | `"relevancy"`, `"popularity"`, `"publishedAt"` |
| `domains` | string | No | Comma-separated domains | `"bbc.co.uk,cnn.com"` |
| `max_articles` | integer | No | Max results (default 100) | `50` |

## Query Syntax

News API supports advanced query syntax:

- **Exact phrase**: `"exact phrase"`
- **OR operator**: `Tesla OR SpaceX`
- **AND operator**: `Tesla AND earnings`
- **NOT operator**: `Tesla NOT stock`
- **Grouping**: `(Tesla OR SpaceX) AND Musk`

## Free Tier Limits

- ✅ 1000 requests per day
- ✅ 100 requests per 15 minutes
- ✅ Articles up to 1 month old
- ✅ 100 results per request

## Rate Limiting

The connector automatically handles rate limiting:
- 10 seconds delay between pages
- Maximum 6 requests per minute (configured)
- Retry logic with exponential backoff

## Evidence Storage

Each article is stored as:
- **Evidence Type**: `news_article`
- **Metadata**: Source name, author, title, description, published date
- **Source URL**: Original article URL
- **Checksum**: SHA-256 hash for deduplication

## Common Use Cases

### Company Due Diligence
```json
{
  "query": "\"Acme Corp\" AND (lawsuit OR investigation OR fraud)",
  "from_date": "2020-01-01",
  "sort_by": "relevancy"
}
```

### Person Background Check
```json
{
  "query": "\"John Smith\" AND (CEO OR executive OR director)",
  "language": "en",
  "max_articles": 100
}
```

### Event Monitoring
```json
{
  "query": "data breach AND (healthcare OR hospital)",
  "from_date": "2024-01-01",
  "sort_by": "publishedAt"
}
```

### Industry Research
```json
{
  "query": "renewable energy AND investment",
  "domains": "reuters.com,bloomberg.com",
  "sort_by": "popularity"
}
```

## Troubleshooting

### Error: "News API key is required"
- Add `NEWS_API_KEY` to your `.env` file
- Get a free key at https://newsapi.org/register

### Error: "Rate limit exceeded"
- Free tier: 1000 requests/day
- Wait 24 hours or upgrade to paid plan
- Check usage at https://newsapi.org/account

### No results found
- Simplify your query
- Extend date range
- Check language parameter
- Try different sort_by options

## Best Practices

1. **Be Specific**: Use exact phrases and boolean operators
2. **Date Range**: Don't search too far back (free tier: 1 month)
3. **Pagination**: Set reasonable `max_articles` limits
4. **Language**: Specify language for better results
5. **Domains**: Filter by trusted news sources

## Python SDK Example

```python
from src.services import IngestionService
from src.models import IngestionJobCreate, SourceType

service = IngestionService()

job = service.create_job(IngestionJobCreate(
    source_type=SourceType.NEWS_API,
    parameters={
        "query": "Tesla OR SpaceX",
        "from_date": "2024-01-01",
        "language": "en",
        "sort_by": "relevancy",
        "max_articles": 50
    }
))

await service.execute_job(job.id)
```

## Links

- 🔑 Get API Key: https://newsapi.org/register
- 📖 Documentation: https://newsapi.org/docs
- 💰 Pricing: https://newsapi.org/pricing
- 🔍 Sources: https://newsapi.org/sources

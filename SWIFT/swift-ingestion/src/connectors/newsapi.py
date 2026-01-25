"""News API connector for news articles and media monitoring."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import EvidenceType, SourceType
from .base import BaseConnector, ConnectorResult


class NewsAPIConnector(BaseConnector):
    """
    Connector for News API (newsapi.org).
    
    Fetches news articles about companies, people, events, and topics.
    
    Free Tier: 1000 requests/day, 100 requests/15 minutes
    
    Configuration:
        - api_key: News API key (get free at https://newsapi.org/register)
        - rate_limit_per_minute: Rate limit (default: 6 for free tier)
        - timeout_seconds: Request timeout (default: 30)
    
    Parameters:
        - query: Search query (required) - company name, person, topic
        - from_date: Start date (YYYY-MM-DD, optional, default: 30 days ago)
        - to_date: End date (YYYY-MM-DD, optional, default: today)
        - language: Language code (optional, e.g., 'en', 'es')
        - sort_by: Sort order (relevancy, popularity, publishedAt)
        - domains: Comma-separated domains to search (optional)
        - page_size: Results per page (max 100, default 20)
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source_type = SourceType.NEWS_API
        self.api_key = config.get('api_key')
        self._client: Optional[httpx.AsyncClient] = None
    
    def validate_config(self) -> bool:
        """Validate News API configuration."""
        if not self.api_key:
            raise ValueError("News API key is required. Get one free at https://newsapi.org/register")
        return True
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.get_timeout(),
                headers={
                    'User-Agent': 'SWIFT-Ingestion/1.0',
                    'X-Api-Key': self.api_key,
                }
            )
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with retry logic."""
        client = await self._get_client()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        self._logger.info(f"Requesting {endpoint}", extra={'params': params})
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Check API response status
        if data.get('status') != 'ok':
            error_msg = data.get('message', 'Unknown error')
            raise ValueError(f"News API error: {error_msg}")
        
        return data
    
    async def fetch(self, parameters: Dict[str, Any]) -> AsyncIterator[ConnectorResult]:
        """
        Fetch news articles from News API.
        
        Args:
            parameters: Must contain 'query', optionally dates, language, etc.
        
        Yields:
            ConnectorResult with news article data
        """
        query = parameters.get('query')
        if not query:
            raise ValueError("query parameter is required")
        
        # Parse date range
        from_date = parameters.get('from_date')
        to_date = parameters.get('to_date')
        
        # Default to last 30 days if no dates specified
        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Build search parameters
        search_params = {
            'q': query,
            'from': from_date,
            'to': to_date,
            'pageSize': parameters.get('page_size', 20),
            'sortBy': parameters.get('sort_by', 'relevancy'),
        }
        
        # Optional parameters
        if parameters.get('language'):
            search_params['language'] = parameters['language']
        if parameters.get('domains'):
            search_params['domains'] = parameters['domains']
        
        try:
            # Search for articles using 'everything' endpoint (more flexible)
            page = 1
            total_results = None
            articles_fetched = 0
            max_articles = parameters.get('max_articles', 100)  # Limit total results
            
            while True:
                search_params['page'] = page
                
                self._logger.info(
                    f"Fetching page {page} for query '{query}'",
                    extra={'page': page, 'query': query}
                )
                
                result = await self._make_request('everything', search_params)
                
                articles = result.get('articles', [])
                
                if total_results is None:
                    total_results = result.get('totalResults', 0)
                    self._logger.info(
                        f"Found {total_results} articles for '{query}'",
                        extra={'total_results': total_results, 'query': query}
                    )
                
                if not articles:
                    break
                
                # Process each article
                for article in articles:
                    if articles_fetched >= max_articles:
                        self._logger.info(
                            f"Reached max articles limit ({max_articles})",
                            extra={'max_articles': max_articles}
                        )
                        return
                    
                    # Parse published date
                    published_at = article.get('publishedAt')
                    source_timestamp = None
                    if published_at:
                        try:
                            source_timestamp = datetime.fromisoformat(
                                published_at.replace('Z', '+00:00')
                            ).isoformat()
                        except Exception:
                            pass
                    
                    # Build metadata
                    metadata = {
                        'source_name': article.get('source', {}).get('name'),
                        'author': article.get('author'),
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'published_at': published_at,
                        'query': query,
                    }
                    
                    yield ConnectorResult(
                        data=article,
                        source_url=article.get('url'),
                        source_identifier=article.get('url'),  # URL as unique identifier
                        source_timestamp=source_timestamp,
                        evidence_type=EvidenceType.NEWS_ARTICLE,
                        metadata=metadata
                    )
                    
                    articles_fetched += 1
                
                # Check if there are more pages
                if len(articles) < search_params['pageSize'] or articles_fetched >= max_articles:
                    break
                
                page += 1
                
                # Rate limiting - be nice to the API (free tier has limits)
                await asyncio.sleep(10)  # 10 seconds between pages
                
        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"HTTP error fetching from News API: {e}",
                extra={'status_code': e.response.status_code, 'query': query}
            )
            
            # Provide helpful error messages
            if e.response.status_code == 401:
                raise ValueError("Invalid News API key. Get one at https://newsapi.org/register")
            elif e.response.status_code == 429:
                raise ValueError("News API rate limit exceeded. Free tier: 1000 requests/day")
            raise
            
        except Exception as e:
            self._logger.error(f"Error fetching from News API: {e}", extra={'query': query})
            raise
    
    async def health_check(self) -> bool:
        """Check if News API is accessible."""
        try:
            # Simple search to verify API access
            params = {
                'q': 'test',
                'pageSize': 1,
            }
            await self._make_request('everything', params)
            return True
        except Exception as e:
            self._logger.error(f"News API health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

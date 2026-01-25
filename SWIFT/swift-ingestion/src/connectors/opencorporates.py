"""OpenCorporates connector for company data."""

import asyncio
from typing import Any, AsyncIterator, Dict, Optional
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import EvidenceType, SourceType
from .base import BaseConnector, ConnectorResult


class OpenCorporatesConnector(BaseConnector):
    """
    Connector for OpenCorporates API.
    
    Fetches company registration data, officers, and filings.
    
    Configuration:
        - api_key: OpenCorporates API key
        - rate_limit_per_minute: Rate limit (default: 60)
        - timeout_seconds: Request timeout (default: 30)
    
    Parameters:
        - company_name: Company name to search (required)
        - jurisdiction_code: Optional jurisdiction filter (e.g., 'us_de', 'gb')
        - include_inactive: Include inactive companies (default: False)
    """
    
    BASE_URL = "https://api.opencorporates.com/v0.4"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source_type = SourceType.OPENCORPORATES
        self.api_key = config.get('api_key')
        self._client: Optional[httpx.AsyncClient] = None
    
    def validate_config(self) -> bool:
        """Validate OpenCorporates configuration."""
        if not self.api_key:
            raise ValueError("OpenCorporates API key is required")
        return True
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.get_timeout(),
                headers={
                    'User-Agent': 'SWIFT-Ingestion/1.0',
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
        
        # Add API key to params
        params['api_token'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        self._logger.info(f"Requesting {endpoint}", extra={'params': params})
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def fetch(self, parameters: Dict[str, Any]) -> AsyncIterator[ConnectorResult]:
        """
        Fetch company data from OpenCorporates.
        
        Args:
            parameters: Must contain 'company_name', optionally 'jurisdiction_code'
        
        Yields:
            ConnectorResult with company data
        """
        company_name = parameters.get('company_name')
        if not company_name:
            raise ValueError("company_name parameter is required")
        
        jurisdiction_code = parameters.get('jurisdiction_code')
        include_inactive = parameters.get('include_inactive', False)
        
        # Search for companies
        search_params = {
            'q': company_name,
            'per_page': 30,
        }
        
        if jurisdiction_code:
            search_params['jurisdiction_code'] = jurisdiction_code
        if not include_inactive:
            search_params['inactive'] = 'false'
        
        try:
            # Search companies
            search_results = await self._make_request('companies/search', search_params)
            
            companies = search_results.get('results', {}).get('companies', [])
            
            self._logger.info(
                f"Found {len(companies)} companies for '{company_name}'",
                extra={'count': len(companies)}
            )
            
            # Fetch detailed data for each company
            for company_data in companies:
                company = company_data.get('company', {})
                company_number = company.get('company_number')
                jurisdiction = company.get('jurisdiction_code')
                
                if not company_number or not jurisdiction:
                    continue
                
                # Fetch full company details
                detail_result = await self._make_request(
                    f'companies/{jurisdiction}/{company_number}',
                    {}
                )
                
                full_company = detail_result.get('results', {}).get('company', {})
                
                # Extract timestamp
                created_at = full_company.get('created_at')
                source_timestamp = None
                if created_at:
                    try:
                        source_timestamp = datetime.fromisoformat(
                            created_at.replace('Z', '+00:00')
                        ).isoformat()
                    except Exception:
                        pass
                
                yield ConnectorResult(
                    data=full_company,
                    source_url=f"https://opencorporates.com/companies/{jurisdiction}/{company_number}",
                    source_identifier=f"{jurisdiction}/{company_number}",
                    source_timestamp=source_timestamp,
                    evidence_type=EvidenceType.COMPANY_RECORD,
                    metadata={
                        'jurisdiction': jurisdiction,
                        'company_number': company_number,
                        'company_name': company.get('name'),
                        'status': company.get('current_status'),
                    }
                )
                
                # Rate limiting
                await asyncio.sleep(1.0)  # Be nice to the API
                
        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"HTTP error fetching from OpenCorporates: {e}",
                extra={'status_code': e.response.status_code}
            )
            raise
        except Exception as e:
            self._logger.error(f"Error fetching from OpenCorporates: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if OpenCorporates API is accessible."""
        try:
            # Simple search to verify API access
            await self._make_request('companies/search', {'q': 'test', 'per_page': 1})
            return True
        except Exception as e:
            self._logger.error(f"OpenCorporates health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

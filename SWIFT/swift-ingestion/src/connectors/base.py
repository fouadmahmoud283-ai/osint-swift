"""Base connector interface for data sources."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel

from ..models import EvidenceType, SourceType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConnectorResult(BaseModel):
    """Result from a connector fetch operation."""
    
    data: Dict[str, Any]
    source_url: Optional[str] = None
    source_identifier: Optional[str] = None
    source_timestamp: Optional[str] = None
    evidence_type: EvidenceType
    metadata: Dict[str, Any] = {}


class BaseConnector(ABC):
    """
    Base class for all data source connectors.
    
    All connectors must implement:
    - fetch(): Retrieve data from the source
    - validate_config(): Ensure connector is properly configured
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connector with configuration.
        
        Args:
            config: Connector-specific configuration
        """
        self.config = config
        self.source_type: SourceType
        self._logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def fetch(self, parameters: Dict[str, Any]) -> AsyncIterator[ConnectorResult]:
        """
        Fetch data from the source.
        
        Args:
            parameters: Search/fetch parameters specific to this connector
        
        Yields:
            ConnectorResult objects containing fetched data
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate connector configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Check if the connector can reach its data source.
        
        Returns:
            True if source is reachable, False otherwise
        """
        try:
            # Default implementation - override in subclasses
            return self.validate_config()
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False
    
    def get_rate_limit(self) -> Optional[int]:
        """
        Get rate limit for this connector (requests per minute).
        
        Returns:
            Rate limit or None if unlimited
        """
        return self.config.get('rate_limit_per_minute')
    
    def get_timeout(self) -> int:
        """
        Get timeout for requests in seconds.
        
        Returns:
            Timeout in seconds
        """
        return self.config.get('timeout_seconds', 30)

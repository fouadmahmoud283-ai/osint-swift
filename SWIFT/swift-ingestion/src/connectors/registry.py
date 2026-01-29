"""Connector registry and factory."""

from typing import Dict, Type

from ..models import SourceType
from ..utils.logging import get_logger
from .base import BaseConnector
from .opencorporates import OpenCorporatesConnector
from .newsapi import NewsAPIConnector
from .osint_search import OsintSearchConnector

logger = get_logger(__name__)


class ConnectorRegistry:
    """Registry for managing available connectors."""
    
    _connectors: Dict[SourceType, Type[BaseConnector]] = {}
    
    @classmethod
    def register(cls, source_type: SourceType, connector_class: Type[BaseConnector]) -> None:
        """Register a connector class."""
        cls._connectors[source_type] = connector_class
        logger.info(
            f"Registered connector: {source_type.value}",
            extra={'source_type': source_type.value, 'class': connector_class.__name__}
        )
    
    @classmethod
    def get_connector(cls, source_type: SourceType, config: Dict) -> BaseConnector:
        """
        Get a connector instance.
        
        Args:
            source_type: Type of source connector
            config: Connector configuration
        
        Returns:
            Configured connector instance
        
        Raises:
            ValueError: If connector type is not registered
        """
        connector_class = cls._connectors.get(source_type)
        
        if not connector_class:
            raise ValueError(
                f"No connector registered for source type: {source_type.value}"
            )
        
        connector = connector_class(config)
        connector.validate_config()
        
        logger.info(
            f"Created connector instance: {source_type.value}",
            extra={'source_type': source_type.value}
        )
        
        return connector
    
    @classmethod
    def list_available(cls) -> list[SourceType]:
        """List all registered connector types."""
        return list(cls._connectors.keys())


# Register built-in connectors
ConnectorRegistry.register(SourceType.OPENCORPORATES, OpenCorporatesConnector)
ConnectorRegistry.register(SourceType.NEWS_API, NewsAPIConnector)
ConnectorRegistry.register(SourceType.OSINT_SEARCH, OsintSearchConnector)

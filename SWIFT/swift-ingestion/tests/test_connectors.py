"""Tests for connector framework."""

import pytest

from src.connectors import ConnectorRegistry
from src.models import SourceType


class TestConnectorRegistry:
    """Tests for ConnectorRegistry."""
    
    def test_get_opencorporates_connector(self):
        """Test getting OpenCorporates connector."""
        config = {
            'api_key': 'test_key',
            'rate_limit_per_minute': 60,
            'timeout_seconds': 30
        }
        
        connector = ConnectorRegistry.get_connector(SourceType.OPENCORPORATES, config)
        
        assert connector is not None
        assert connector.source_type == SourceType.OPENCORPORATES
    
    def test_invalid_connector_type(self):
        """Test getting invalid connector type."""
        with pytest.raises(ValueError):
            # This will fail because NEWS_API is not registered yet
            ConnectorRegistry.get_connector(SourceType.NEWS_API, {})
    
    def test_list_available_connectors(self):
        """Test listing available connectors."""
        available = ConnectorRegistry.list_available()
        
        assert SourceType.OPENCORPORATES in available

"""Tests for News API connector."""

import pytest
from datetime import datetime, timedelta

from src.connectors import NewsAPIConnector
from src.models import EvidenceType, SourceType


class TestNewsAPIConnector:
    """Tests for NewsAPIConnector."""
    
    def test_connector_initialization(self):
        """Test connector initialization."""
        config = {
            'api_key': 'test_key',
            'rate_limit_per_minute': 6,
            'timeout_seconds': 30
        }
        
        connector = NewsAPIConnector(config)
        
        assert connector.source_type == SourceType.NEWS_API
        assert connector.api_key == 'test_key'
    
    def test_validate_config_with_api_key(self):
        """Test config validation with API key."""
        config = {'api_key': 'test_key'}
        connector = NewsAPIConnector(config)
        
        assert connector.validate_config() is True
    
    def test_validate_config_without_api_key(self):
        """Test config validation without API key."""
        config = {}
        connector = NewsAPIConnector(config)
        
        with pytest.raises(ValueError, match="News API key is required"):
            connector.validate_config()
    
    @pytest.mark.asyncio
    async def test_fetch_requires_query(self):
        """Test that fetch requires a query parameter."""
        config = {'api_key': 'test_key'}
        connector = NewsAPIConnector(config)
        
        with pytest.raises(ValueError, match="query parameter is required"):
            async for _ in connector.fetch({}):
                pass
    
    def test_get_rate_limit(self):
        """Test rate limit configuration."""
        config = {
            'api_key': 'test_key',
            'rate_limit_per_minute': 10
        }
        connector = NewsAPIConnector(config)
        
        assert connector.get_rate_limit() == 10
    
    def test_get_timeout(self):
        """Test timeout configuration."""
        config = {
            'api_key': 'test_key',
            'timeout_seconds': 45
        }
        connector = NewsAPIConnector(config)
        
        assert connector.get_timeout() == 45

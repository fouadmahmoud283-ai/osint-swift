"""Connectors for external data sources."""

from .base import BaseConnector, ConnectorResult
from .opencorporates import OpenCorporatesConnector
from .newsapi import NewsAPIConnector
from .registry import ConnectorRegistry

__all__ = [
    'BaseConnector',
    'ConnectorResult',
    'OpenCorporatesConnector',
    'NewsAPIConnector',
    'ConnectorRegistry',
]

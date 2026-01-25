"""Shared models for SWIFT API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of an ingestion job."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Type of data source."""
    
    OPENCORPORATES = "opencorporates"
    NEWS_API = "news_api"
    RSS_FEED = "rss_feed"
    WEB_SCRAPER = "web_scraper"
    MANUAL_UPLOAD = "manual_upload"


class EvidenceType(str, Enum):
    """Type of evidence document."""
    
    COMPANY_RECORD = "company_record"
    NEWS_ARTICLE = "news_article"
    SOCIAL_MEDIA_POST = "social_media_post"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    OTHER = "other"

"""OSINT search connector for digital footprint discovery."""

import asyncio
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

from apify_client import ApifyClient

from ..models import EvidenceType, SourceType
from .base import BaseConnector, ConnectorResult


class OsintSearchConnector(BaseConnector):
    """
    Connector for OSINT search using an external automation actor.

    Configuration:
        - api_token: API token
        - actor_id: Actor identifier
        - timeout_seconds: Request timeout (default: 30)

    Parameters:
        - searchQuery: Search string (required)
        - searchType: Type of search (required, e.g., email, username)
        - scanDepth: "standard" or "deep" (default: standard)
        - categories: list of categories (default: [])
        - exportFormats: list of export formats (default: ["json"])
        - extractData: bool (default: True)
        - recursiveSearch: bool (default: False)
        - reportSorting: "default" (default)
        - timeout: int minutes (default: 15)
        - maxConcurrency: int (default: 50)
        - retries: int (default: 1)
        - printErrors: bool (default: False)
        - proxyConfiguration: object or None (default: None)
    """

    DEFAULT_ACTOR_ID = "mqNu8WBvuKXgZRt4M"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source_type = SourceType.OSINT_SEARCH
        self.api_token = config.get("api_token")
        self.actor_id = config.get("actor_id", self.DEFAULT_ACTOR_ID)
        self._client: Optional[ApifyClient] = None

    def validate_config(self) -> bool:
        if not self.api_token:
            raise ValueError("OSINT search API token is required")
        if not self.actor_id:
            raise ValueError("OSINT search actor_id is required")
        return True

    def _get_client(self) -> ApifyClient:
        if self._client is None:
            self._client = ApifyClient(self.api_token)
        return self._client

    async def _run_actor(self, run_input: Dict[str, Any]) -> Dict[str, Any]:
        client = self._get_client()
        return await asyncio.to_thread(
            lambda: client.actor(self.actor_id).call(run_input=run_input)
        )

    async def _iterate_dataset(self, dataset_id: str):
        client = self._get_client()
        return await asyncio.to_thread(
            lambda: list(client.dataset(dataset_id).iterate_items())
        )

    async def fetch(self, parameters: Dict[str, Any]) -> AsyncIterator[ConnectorResult]:
        search_query = parameters.get("searchQuery")
        search_type = parameters.get("searchType")
        if not search_query or not search_type:
            raise ValueError("searchQuery and searchType are required")

        run_input = {
            "searchQuery": search_query,
            "searchType": search_type,
            "scanDepth": parameters.get("scanDepth", "standard"),
            "categories": parameters.get("categories", []),
            "extractData": parameters.get("extractData", True),
            "recursiveSearch": parameters.get("recursiveSearch", False),
            "exportFormats": parameters.get("exportFormats", ["json"]),
            "reportSorting": parameters.get("reportSorting", "default"),
            "timeout": parameters.get("timeout", 15),
            "maxConcurrency": parameters.get("maxConcurrency", 50),
            "retries": parameters.get("retries", 1),
            "printErrors": parameters.get("printErrors", False),
            "proxyConfiguration": parameters.get("proxyConfiguration"),
        }

        run = await self._run_actor(run_input)
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            raise ValueError("OSINT search run did not return a dataset id")

        items = await self._iterate_dataset(dataset_id)
        fetched_at = datetime.utcnow().isoformat()

        for item in items:
            source_url = None
            if isinstance(item, dict):
                source_url = item.get("url") or item.get("profileUrl") or item.get("sourceUrl")

            yield ConnectorResult(
                data=item,
                source_url=source_url,
                source_identifier=source_url,
                source_timestamp=fetched_at,
                evidence_type=EvidenceType.RAW_DATA,
                metadata={
                    "search_query": search_query,
                    "search_type": search_type,
                    "scan_depth": run_input.get("scanDepth"),
                    "categories": run_input.get("categories"),
                },
            )

    async def close(self) -> None:
        self._client = None

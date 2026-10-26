"""Meilisearch client provider and health checker."""

from typing import Optional

from app.config import settings
from app.core.logging import logger
from meilisearch import Client

_client: Optional[Client] = None


def get_meili_client() -> Client:
    """Returns a singleton instance of the Meilisearch client."""
    global _client
    if _client is None:
        _client = Client(
            url=settings.meili_http_addr,
            api_key=settings.meili_master_key,
            timeout=settings.meili_timeout_ms / 1000.0,
        )
    return _client


# Alias for compatibility
get_meilisearch_client = get_meili_client


def check_meili_health() -> bool:
    """Checks whether the Meilisearch service is healthy and responsive."""
    try:
        client = get_meili_client()
        health = client.health()
        return health.get("status") == "available"
    except Exception as e:
        logger.warning(f"Meilisearch health check failed: {e}")
        return False

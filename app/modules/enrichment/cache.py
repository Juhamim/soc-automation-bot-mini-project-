from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class EnrichmentCache:
    """
    Redis-backed cache for enrichment results.
    Key format: enrich:{provider}:{observable_value}
    TTL: configurable via ENRICHMENT_CACHE_TTL (default 24h)
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._client

    def _key(self, provider: str, value: str) -> str:
        # Sanitize value to avoid Redis key issues
        safe_value = value.replace(" ", "_").replace("/", "_")
        return f"enrich:{provider}:{safe_value}"

    def get(self, provider: str, value: str) -> Optional[Dict[str, Any]]:
        """Return cached enrichment result or None if not found / expired."""
        try:
            raw = self._get_client().get(self._key(provider, value))
            if raw:
                logger.debug(f"[Cache] HIT for {provider}:{value}")
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"[Cache] GET error: {e}")
        return None

    def set(self, provider: str, value: str, result: Dict[str, Any]) -> None:
        """Store an enrichment result in Redis with TTL."""
        try:
            self._get_client().setex(
                name=self._key(provider, value),
                time=settings.ENRICHMENT_CACHE_TTL,
                value=json.dumps(result, default=str),
            )
            logger.debug(f"[Cache] SET for {provider}:{value} (TTL={settings.ENRICHMENT_CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"[Cache] SET error: {e}")

    def invalidate(self, provider: str, value: str) -> None:
        """Remove a cached entry."""
        try:
            self._get_client().delete(self._key(provider, value))
        except Exception as e:
            logger.warning(f"[Cache] DELETE error: {e}")

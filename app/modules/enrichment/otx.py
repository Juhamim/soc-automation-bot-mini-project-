from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.modules.enrichment.base import BaseEnricher

logger = logging.getLogger(__name__)

OTX_API_BASE = "https://otx.alienvault.com/api/v1"


class OTXEnricher(BaseEnricher):
    """
    AlienVault OTX API integration.
    Supports: IP, domain, file hash indicator lookups.
    Falls back to mock when OTX_API_KEY=MOCK.
    """

    @property
    def provider_name(self) -> str:
        return "AlienVaultOTX"

    def enrich(self, observable_type: str, value: str) -> Dict[str, Any]:
        if settings.is_mock("OTX_API_KEY"):
            logger.debug(f"[OTX] Mock mode for {value}")
            return self._mock_response(observable_type, value)

        try:
            url = self._get_url(observable_type, value)
            if not url:
                return self._mock_response(observable_type, value)

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    url,
                    headers={"X-OTX-API-KEY": settings.OTX_API_KEY},
                )
                response.raise_for_status()
                data = response.json()

            return self._parse_response(observable_type, value, data)

        except Exception as e:
            logger.error(f"[OTX] Error for {value}: {e}")
            return self._mock_response(observable_type, value)

    def _get_url(self, observable_type: str, value: str) -> str | None:
        if observable_type == "ip":
            return f"{OTX_API_BASE}/indicators/IPv4/{value}/general"
        elif observable_type == "domain":
            return f"{OTX_API_BASE}/indicators/domain/{value}/general"
        elif observable_type == "hash":
            return f"{OTX_API_BASE}/indicators/file/{value}/general"
        return None

    def _parse_response(self, observable_type: str, value: str, data: dict) -> Dict[str, Any]:
        pulse_count = data.get("pulse_info", {}).get("count", 0)
        reputation_score = min(round(pulse_count / 10, 2), 1.0)
        return {
            "is_mock": False,
            "provider": self.provider_name,
            "observable_type": observable_type,
            "observable_value": value,
            "reputation_score": reputation_score,
            "pulse_count": pulse_count,
            "is_malicious": pulse_count > 3,
            "tags": data.get("pulse_info", {}).get("related_indicator_is_active", []),
        }

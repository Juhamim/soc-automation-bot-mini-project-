from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.modules.enrichment.base import BaseEnricher

logger = logging.getLogger(__name__)

ABUSEIPDB_API_BASE = "https://api.abuseipdb.com/api/v2"


class AbuseIPDBEnricher(BaseEnricher):
    """
    AbuseIPDB v2 API integration.
    Supports: IP address reputation checks only.
    Falls back to mock when ABUSEIPDB_API_KEY=MOCK.
    """

    @property
    def provider_name(self) -> str:
        return "AbuseIPDB"

    def enrich(self, observable_type: str, value: str) -> Dict[str, Any]:
        # AbuseIPDB only supports IP lookups
        if observable_type != "ip":
            return {
                "is_mock": True,
                "provider": self.provider_name,
                "observable_type": observable_type,
                "observable_value": value,
                "reputation_score": 0.0,
                "note": f"AbuseIPDB does not support {observable_type} lookups",
            }

        if settings.is_mock("ABUSEIPDB_API_KEY"):
            logger.debug(f"[AbuseIPDB] Mock mode for {value}")
            return self._mock_response(observable_type, value)

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{ABUSEIPDB_API_BASE}/check",
                    headers={
                        "Key": settings.ABUSEIPDB_API_KEY,
                        "Accept": "application/json",
                    },
                    params={"ipAddress": value, "maxAgeInDays": 90, "verbose": ""},
                )
                response.raise_for_status()
                data = response.json().get("data", {})

            abuse_confidence = data.get("abuseConfidenceScore", 0)
            reputation_score = round(abuse_confidence / 100, 2)

            return {
                "is_mock": False,
                "provider": self.provider_name,
                "observable_type": observable_type,
                "observable_value": value,
                "reputation_score": reputation_score,
                "abuse_confidence_score": abuse_confidence,
                "total_reports": data.get("totalReports", 0),
                "country_code": data.get("countryCode"),
                "isp": data.get("isp"),
                "is_whitelisted": data.get("isWhitelisted", False),
                "is_malicious": abuse_confidence > 50,
            }

        except httpx.HTTPStatusError as e:
            logger.warning(f"[AbuseIPDB] HTTP error for {value}: {e.response.status_code}")
            return self._mock_response(observable_type, value)
        except Exception as e:
            logger.error(f"[AbuseIPDB] Error for {value}: {e}")
            return self._mock_response(observable_type, value)

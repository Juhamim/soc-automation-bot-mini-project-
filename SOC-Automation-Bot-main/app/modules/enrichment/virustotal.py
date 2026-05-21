from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.modules.enrichment.base import BaseEnricher

logger = logging.getLogger(__name__)

VT_API_BASE = "https://www.virustotal.com/api/v3"


class VirusTotalEnricher(BaseEnricher):
    """
    VirusTotal v3 API integration.
    Supports: IP, domain, file hash, URL lookups.
    Falls back to mock when VIRUSTOTAL_API_KEY=MOCK.
    """

    @property
    def provider_name(self) -> str:
        return "VirusTotal"

    def enrich(self, observable_type: str, value: str) -> Dict[str, Any]:
        if settings.is_mock("VIRUSTOTAL_API_KEY"):
            logger.debug(f"[VT] Mock mode — returning simulated result for {value}")
            return self._mock_response(observable_type, value)

        try:
            endpoint = self._get_endpoint(observable_type, value)
            if not endpoint:
                return self._mock_response(observable_type, value)

            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    endpoint,
                    headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
                )
                response.raise_for_status()
                data = response.json()

            return self._parse_response(observable_type, value, data)

        except httpx.HTTPStatusError as e:
            logger.warning(f"[VT] HTTP error for {value}: {e.response.status_code}")
            return self._mock_response(observable_type, value)
        except Exception as e:
            logger.error(f"[VT] Unexpected error for {value}: {e}")
            return self._mock_response(observable_type, value)

    def _get_endpoint(self, observable_type: str, value: str) -> str | None:
        if observable_type == "ip":
            return f"{VT_API_BASE}/ip_addresses/{value}"
        elif observable_type == "domain":
            return f"{VT_API_BASE}/domains/{value}"
        elif observable_type == "hash":
            return f"{VT_API_BASE}/files/{value}"
        elif observable_type == "url":
            import base64
            encoded = base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")
            return f"{VT_API_BASE}/urls/{encoded}"
        return None

    def _parse_response(self, observable_type: str, value: str, data: dict) -> Dict[str, Any]:
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total = sum(stats.values()) or 1
        reputation_score = round((malicious + suspicious * 0.5) / total, 2)

        return {
            "is_mock": False,
            "provider": self.provider_name,
            "observable_type": observable_type,
            "observable_value": value,
            "reputation_score": reputation_score,
            "detections": malicious,
            "total_engines": total,
            "is_malicious": malicious > 5,
            "raw_stats": stats,
        }

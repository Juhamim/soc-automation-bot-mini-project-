from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseEnricher(ABC):
    """
    Abstract base class for all threat intelligence enrichment providers.
    Each provider must implement the `enrich` method and expose a `provider_name`.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier (e.g. 'VirusTotal', 'AbuseIPDB')."""
        ...

    @abstractmethod
    def enrich(self, observable_type: str, value: str) -> Dict[str, Any]:
        """
        Query the threat intelligence provider for the given observable.

        Args:
            observable_type: 'ip', 'domain', 'hash', or 'url'
            value: The observable value to query.

        Returns:
            A dict with at minimum:
                - 'is_mock': bool
                - 'reputation_score': float (0.0 = clean, 1.0 = malicious)
                - 'provider': str
                - Any provider-specific fields
        """
        ...

    def _mock_response(self, observable_type: str, value: str) -> Dict[str, Any]:
        """
        Return a plausible mock response when the API key is not configured.
        Uses the observable value to generate a deterministic score.
        """
        import hashlib
        seed = int(hashlib.md5(value.encode()).hexdigest(), 16)
        # Score biased toward detection (30% chance of being flagged)
        score = round((seed % 100) / 100, 2)
        detections = int(score * 20)
        return {
            "is_mock": True,
            "provider": self.provider_name,
            "observable_type": observable_type,
            "observable_value": value,
            "reputation_score": score,
            "detections": detections,
            "total_engines": 70,
            "is_malicious": score > 0.5,
            "note": f"[MOCK] Real API key not configured for {self.provider_name}",
        }

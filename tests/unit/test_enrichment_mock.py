import pytest
from app.modules.enrichment.virustotal import VirusTotalEnricher
from app.modules.enrichment.abuseipdb import AbuseIPDBEnricher
from app.modules.enrichment.otx import OTXEnricher
from app.core.config import Settings


@pytest.fixture(autouse=True)
def force_mock_keys(monkeypatch):
    """Force enrichers to use mock mode even when real API keys exist in env."""
    def always_mock(self, key_name):
        return True
    monkeypatch.setattr(Settings, "is_mock", always_mock)


# All tests run in mock mode (API keys = MOCK in test environment)


def test_virustotal_ip_mock():
    enricher = VirusTotalEnricher()
    result = enricher.enrich("ip", "45.33.32.156")
    assert result["is_mock"] is True
    assert result["provider"] == "VirusTotal"
    assert 0.0 <= result["reputation_score"] <= 1.0


def test_virustotal_hash_mock():
    enricher = VirusTotalEnricher()
    result = enricher.enrich("hash", "d41d8cd98f00b204e9800998ecf8427e")
    assert result["is_mock"] is True
    assert "detections" in result


def test_abuseipdb_ip_mock():
    enricher = AbuseIPDBEnricher()
    result = enricher.enrich("ip", "1.2.3.4")
    assert result["is_mock"] is True
    assert result["provider"] == "AbuseIPDB"
    assert 0.0 <= result["reputation_score"] <= 1.0


def test_abuseipdb_non_ip_skips():
    enricher = AbuseIPDBEnricher()
    result = enricher.enrich("domain", "evil.com")
    assert result["reputation_score"] == 0.0
    assert "does not support" in result["note"]


def test_otx_ip_mock():
    enricher = OTXEnricher()
    result = enricher.enrich("ip", "8.8.8.8")
    assert result["is_mock"] is True
    assert result["provider"] == "AlienVaultOTX"


def test_mock_scores_are_deterministic():
    """Same input should always produce the same score."""
    enricher = VirusTotalEnricher()
    r1 = enricher.enrich("ip", "192.168.1.100")
    r2 = enricher.enrich("ip", "192.168.1.100")
    assert r1["reputation_score"] == r2["reputation_score"]

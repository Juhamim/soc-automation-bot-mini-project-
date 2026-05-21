import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import settings

client = TestClient(app)
AUTH = {"X-API-Key": settings.API_KEY}

SAMPLE_ALERT = {
    "source": "Wazuh",
    "event_type": "brute_force",
    "src_ip": "45.33.32.156",
    "severity": "High",
    "external_id": "wazuh-1234",
}


def test_health_check():
    """Health endpoint should return 200 without auth."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_alert_success():
    """Valid alert with correct API key → 202 Accepted."""
    with patch("app.api.routes.crud.create_alert") as mock_create, \
         patch("app.api.routes.process_alert") as mock_task:
        mock_create.return_value = MagicMock(id="test-alert-uuid-1234")
        mock_task.delay.return_value = MagicMock(id="test-job-uuid-5678")

        response = client.post("/api/v1/alert", json=SAMPLE_ALERT, headers=AUTH)
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "accepted"
        assert "job_id" in body
        assert "alert_id" in body


def test_ingest_alert_missing_api_key():
    """Missing API key → 401 Unauthorized."""
    response = client.post("/api/v1/alert", json=SAMPLE_ALERT)
    assert response.status_code == 401


def test_ingest_alert_invalid_api_key():
    """Wrong API key → 403 Forbidden."""
    response = client.post(
        "/api/v1/alert",
        json=SAMPLE_ALERT,
        headers={"X-API-Key": "wrong-key-here"},
    )
    assert response.status_code == 403


def test_ingest_alert_missing_source_field():
    """Missing required 'source' field → 422 Unprocessable Entity."""
    bad_payload = {"event_type": "brute_force", "src_ip": "1.2.3.4"}
    response = client.post("/api/v1/alert", json=bad_payload, headers=AUTH)
    assert response.status_code == 422


def test_get_alert_not_found():
    """Non-existent alert ID → 404."""
    with patch("app.api.routes.crud.get_alert", return_value=None):
        response = client.get("/api/v1/alerts/nonexistent-uuid", headers=AUTH)
        assert response.status_code == 404


def test_metrics_endpoint():
    """Metrics endpoint returns expected shape."""
    with patch("app.api.routes.crud.get_metrics") as mock_metrics:
        mock_metrics.return_value = {
            "total_alerts": 10,
            "by_status": {"New": 5, "Closed": 5},
            "by_severity": {"High": 3, "Low": 7},
            "average_risk_score": 55.0,
        }
        response = client.get("/api/v1/metrics", headers=AUTH)
        assert response.status_code == 200
        body = response.json()
        assert body["total_alerts"] == 10

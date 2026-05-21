import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.api.main import app
from app.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": settings.API_KEY}


@pytest.fixture
def mock_db():
    return MagicMock()

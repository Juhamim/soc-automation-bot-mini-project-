from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration — all values are read from environment variables
    or the .env file. Defaults are safe for local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_KEY: str = "dev-secret-key-change-in-production"
    SECRET_KEY: str = "change-me-to-a-random-32-char-string"

    # ── Database ───────────────────────────────────────────────────────────────
    POSTGRES_USER: str = "socadmin"
    POSTGRES_PASSWORD: str = "socpassword"
    POSTGRES_DB: str = "socdb"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://socadmin:socpassword@postgres:5432/socdb"

    # ── Redis / Celery ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # ── Threat Intelligence APIs ───────────────────────────────────────────────
    VIRUSTOTAL_API_KEY: str = "MOCK"
    ABUSEIPDB_API_KEY: str = "MOCK"
    OTX_API_KEY: str = "MOCK"
    ENRICHMENT_CACHE_TTL: int = 86400  # 24h

    # ── Notifications ──────────────────────────────────────────────────────────
    SLACK_WEBHOOK_URL: str = "MOCK"
    SLACK_ALERT_CHANNEL: str = "#security-alerts"

    # ── Ticketing ──────────────────────────────────────────────────────────────
    JIRA_URL: str = "MOCK"
    JIRA_EMAIL: str = "MOCK"
    JIRA_API_TOKEN: str = "MOCK"
    JIRA_PROJECT_KEY: str = "SOC"

    # ── Firewall / Blocking ───────────────────────────────────────────────────
    FIREWALL_ALLOW_EXECUTION: bool = False

    # ── Risk Thresholds ────────────────────────────────────────────────────────
    RISK_SCORE_LOW_THRESHOLD: int = 20
    RISK_SCORE_MEDIUM_THRESHOLD: int = 40
    RISK_SCORE_HIGH_THRESHOLD: int = 70
    RISK_SCORE_CRITICAL_THRESHOLD: int = 90

    def is_mock(self, key_name: str) -> bool:
        """Helper: check if a key is still set to MOCK value."""
        return getattr(self, key_name, "MOCK") == "MOCK"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


settings = get_settings()

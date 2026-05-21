from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.database.models import SystemSettings
from app.database.session import SessionLocal

_DEFAULT_SETTINGS: Dict[str, Dict[str, Any]] = {
    "general": {
        "organization_name": "Acme Corporation",
        "time_zone": "UTC (GMT+0:00)",
        "date_format": "MM/DD/YYYY",
        "language": "English (US)",
    },
    "notifications": {
        "critical_alerts": True,
        "incident_updates": True,
        "playbook_failures": True,
        "weekly_reports": True,
        "email": "admin@acme.com",
    },
    "security": {
        "two_factor_enabled": True,
        "session_timeout_minutes": 30,
        "password_min_length": 12,
        "require_special_chars": True,
    },
}


def _get_or_create(db: Session) -> SystemSettings:
    row = db.query(SystemSettings).first()
    if not row:
        row = SystemSettings(payload=deepcopy(_DEFAULT_SETTINGS))
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_system_settings() -> Dict[str, Dict[str, Any]]:
    db: Session = SessionLocal()
    try:
        row = _get_or_create(db)
        return deepcopy(row.payload)
    finally:
        db.close()


def update_system_settings(patch: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    db: Session = SessionLocal()
    try:
        row = _get_or_create(db)
        payload = deepcopy(row.payload)
        for section, values in patch.items():
            if section not in payload or not isinstance(values, dict):
                continue
            payload[section].update(values)
        row.payload = payload
        db.commit()
        db.refresh(row)
        return deepcopy(row.payload)
    finally:
        db.close()

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


# ─── Auth Models ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "Analyst"


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# ─── Request Models ───────────────────────────────────────────────────────────

class AlertIngestionRequest(BaseModel):
    """Payload for POST /api/v1/alert"""
    source: str = Field(..., description="Source system (e.g. 'Wazuh', 'Splunk', 'Generic')")
    event_type: Optional[str] = Field(None, description="Type of event (e.g. 'brute_force')")
    severity: Optional[str] = Field(None, description="Initial severity from source")
    src_ip: Optional[str] = Field(None, description="Source IP address")
    dest_ip: Optional[str] = Field(None, description="Destination IP address")
    domain: Optional[str] = Field(None, description="Domain name involved")
    file_hash: Optional[str] = Field(None, description="File hash (MD5/SHA256)")
    external_id: Optional[str] = Field(None, description="ID from source system")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Full raw alert payload")

    class Config:
        extra = "allow"  # Accept any extra fields from various SIEMs


class ManualActionRequest(BaseModel):
    """Payload for manual action trigger"""
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    executed_by: Optional[str] = Field("analyst", description="User triggering the action")


# ─── Response Models ──────────────────────────────────────────────────────────

class AlertIngestionResponse(BaseModel):
    job_id: str
    alert_id: str
    status: str
    message: str


class EnrichmentResultResponse(BaseModel):
    id: UUID
    observable_type: str
    observable_value: str
    source_provider: str
    reputation_score: Optional[float]
    queried_at: datetime

    class Config:
        from_attributes = True


class ActionLogResponse(BaseModel):
    id: UUID
    action_name: str
    status: str
    output_log: Optional[str]
    executed_at: datetime
    executed_by: str

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: UUID
    source_integration: str
    external_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    risk_score: Optional[int]
    severity: Optional[str]
    status: str
    normalized_data: Optional[Dict[str, Any]]
    enrichment_results: List[EnrichmentResultResponse] = []
    action_logs: List[ActionLogResponse] = []

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    total: int
    page: int
    limit: int
    alerts: List[AlertResponse]


class MetricsResponse(BaseModel):
    total_alerts: int
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    average_risk_score: float


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    environment: str

# ─── Playbook Models ──────────────────────────────────────────────────────────

class PlaybookResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    trigger_severity: Optional[List[str]] = Field(default_factory=list)
    steps_definition: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        from_attributes = True

class PlaybookCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    trigger_severity: List[str]
    steps_definition: Dict[str, Any]

class PlaybookToggleRequest(BaseModel):
    is_active: bool

class ExecutionResponse(BaseModel):
    id: UUID
    playbook: str
    action_name: str
    timestamp: str
    trigger: str
    status: str
    duration: str

# ─── Reporting Models ─────────────────────────────────────────────────────────

class ReportGenerationRequest(BaseModel):
    timeframe: str = Field(default="Ad-Hoc", description="Title for the report timeframe")
    hours: int = Field(default=24, ge=1, le=720, description="Hours to look back")

class ReportGenerationResponse(BaseModel):
    status: str
    timeframe: str
    job_id: str
    message: str

# ─── Incident Models ──────────────────────────────────────────────────────────

class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    severity: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    assignee: Optional[str]
    category: Optional[str]
    alert_count: int

    class Config:
        from_attributes = True


class IncidentCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    severity: Optional[str] = None
    status: str = "Open"
    assignee: Optional[str] = None
    category: Optional[str] = None


class IncidentListResponse(BaseModel):
    total: int
    incidents: List[IncidentResponse]

# ─── Threat Intel Models ──────────────────────────────────────────────────────

class ThreatIntelResponse(BaseModel):
    id: UUID
    indicator_type: str
    indicator_value: str
    risk_level: str
    country: Optional[str]
    first_seen: datetime
    last_seen: Optional[datetime]
    occurrences: int

    class Config:
        from_attributes = True

class ThreatIntelListResponse(BaseModel):
    total: int
    threats: List[ThreatIntelResponse]

# ─── Settings / Integrations Models ───────────────────────────────────────────

class SettingsGeneral(BaseModel):
    organization_name: str
    time_zone: str
    date_format: str
    language: str


class SettingsNotifications(BaseModel):
    critical_alerts: bool
    incident_updates: bool
    playbook_failures: bool
    weekly_reports: bool
    email: str


class SettingsSecurity(BaseModel):
    two_factor_enabled: bool
    session_timeout_minutes: int
    password_min_length: int
    require_special_chars: bool


class SettingsResponse(BaseModel):
    general: SettingsGeneral
    notifications: SettingsNotifications
    security: SettingsSecurity


class SettingsUpdateRequest(BaseModel):
    general: Optional[SettingsGeneral] = None
    notifications: Optional[SettingsNotifications] = None
    security: Optional[SettingsSecurity] = None


class IntegrationItem(BaseModel):
    name: str
    description: str
    status: str
    status_detail: Optional[str] = None


class IntegrationsResponse(BaseModel):
    integrations: List[IntegrationItem]


class ApiKeyItem(BaseModel):
    name: str
    key: str
    status: Optional[str] = None
    created: Optional[str] = None
    last_used: Optional[str] = None


class ApiKeysResponse(BaseModel):
    keys: List[ApiKeyItem]

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.api.auth import get_current_user, get_current_user_or_api_key
from app.api.models import (
    Token,
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    AlertIngestionRequest,
    AlertIngestionResponse,
    AlertResponse,
    AlertListResponse,
    MetricsResponse,
    ManualActionRequest,
    PlaybookResponse,
    PlaybookCreateRequest,
    PlaybookToggleRequest,
    ExecutionResponse,
    ReportGenerationRequest,
    ReportGenerationResponse,
    IncidentResponse,
    IncidentCreateRequest,
    IncidentListResponse,
    ThreatIntelResponse,
    ThreatIntelListResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    IntegrationsResponse,
    ApiKeysResponse,
)
from app.database.session import get_db
from app.database import crud
from app.database.models import User
from app.core.tasks import process_alert
from app.core.security import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
)
from app.core.config import settings as app_settings
from app.core.system_settings import get_system_settings, update_system_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Authentication ───────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse, tags=["Auth"])
async def read_users_me(current_user: User = Depends(get_current_user_or_api_key)):
    return current_user


# ─── Alert Ingestion ──────────────────────────────────────────────────────────

@router.post(
    "/alert",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AlertIngestionResponse,
    summary="Ingest a new security alert",
    tags=["Ingestion"],
)
async def ingest_alert(
    payload: AlertIngestionRequest,
    db: Session = Depends(get_db),
    # Ingestion might still use an API Key in a real scenario, but we'll secure it with JWT for now
    current_user: User = Depends(get_current_user_or_api_key),
):
    """
    Accepts a security alert from any source (Wazuh, Splunk, Generic webhook).
    Returns 202 Accepted immediately and queues processing via Celery.
    """
    # Build raw_data from payload (merge extra fields)
    raw = payload.model_dump(exclude_none=False)
    if payload.raw_data:
        raw.update(payload.raw_data)

    alert = crud.create_alert(
        db=db,
        source_integration=payload.source,
        raw_data=raw,
        external_id=payload.external_id,
    )

    # Queue the processing task
    task = process_alert.delay(str(alert.id))
    logger.info(f"[API] Alert {alert.id} queued as task {task.id}")

    return AlertIngestionResponse(
        job_id=task.id,
        alert_id=str(alert.id),
        status="accepted",
        message="Alert queued for processing.",
    )


# ─── Alert Listing ────────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="List all alerts with filtering and pagination",
    tags=["Alerts"],
)
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    date_start: Optional[datetime] = Query(None),
    date_end: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    alerts, total = crud.list_alerts(
        db,
        page=page,
        limit=limit,
        status=status_filter,
        severity=severity,
        date_start=date_start,
        date_end=date_end,
    )
    return AlertListResponse(
        total=total,
        page=page,
        limit=limit,
        alerts=alerts,
    )


# ─── Alert Detail ─────────────────────────────────────────────────────────────

@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    summary="Get full details of a specific alert",
    tags=["Alerts"],
)
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


# ─── Manual Action Trigger ────────────────────────────────────────────────────

@router.post(
    "/alerts/{alert_id}/actions/{action_name}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Manually trigger a response action on an alert",
    tags=["Actions"],
)
async def trigger_action(
    alert_id: str,
    action_name: str,
    body: ManualActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    supported_actions = ["block_ip", "notify_slack", "create_jira_ticket", "isolate_host"]
    if action_name not in supported_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported action '{action_name}'. Supported: {supported_actions}",
        )

    # Dispatch action
    from app.modules.response.playbook_engine import PlaybookEngine
    engine = PlaybookEngine(db=db, alert_id=alert_id)
    result = engine.run_single_action(
        action_name=action_name,
        params=body.parameters,
        executed_by=body.executed_by or "analyst",
    )

    return {
        "alert_id": alert_id,
        "action": action_name,
        "result": result,
    }


# ─── Metrics ──────────────────────────────────────────────────────────────────

@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Get system-wide alert metrics",
    tags=["Dashboard"],
)
async def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    return crud.get_metrics(db)

# ─── Playbooks ────────────────────────────────────────────────────────────────

@router.get(
    "/playbooks/executions",
    response_model=list[ExecutionResponse],
    summary="List recent playbook action executions",
    tags=["Playbooks"],
)
async def list_recent_executions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    return crud.get_recent_executions(db, limit=limit)


@router.get(
    "/playbooks",
    response_model=list[PlaybookResponse],
    summary="List all playbooks",
    tags=["Playbooks"],
)
async def list_playbooks(
    include_inactive: bool = Query(True, description="Include inactive playbooks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    return crud.get_playbooks(db, include_inactive=include_inactive)

@router.post(
    "/playbooks",
    response_model=PlaybookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new specific playbook from the visual builder",
    tags=["Playbooks"],
)
async def create_playbook(
    payload: PlaybookCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    try:
        return crud.create_playbook(db, payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create playbook. Playbook Name might already exist. Error: {str(e)}")

@router.post(
    "/playbooks/{playbook_id}/toggle",
    response_model=PlaybookResponse,
    summary="Enable or disable a playbook",
    tags=["Playbooks"],
)
async def toggle_playbook(
    playbook_id: str,
    payload: PlaybookToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    playbook = crud.toggle_playbook(db, playbook_id, payload.is_active)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return playbook

# ─── Reporting ────────────────────────────────────────────────────────────────

@router.post(
    "/reports/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportGenerationResponse,
    summary="Trigger an ad-hoc SOC report generation",
    tags=["Reporting"],
)
async def generate_report(
    payload: ReportGenerationRequest,
    current_user: User = Depends(get_current_user_or_api_key),
):
    from app.core.tasks import generate_and_send_report
    
    # Queue the Celery task
    task = generate_and_send_report.delay(timeframe=payload.timeframe, hours=payload.hours)
    
    return ReportGenerationResponse(
        status="accepted",
        timeframe=payload.timeframe,
        job_id=task.id,
        message="Reporting task queued successfully."
    )

# ─── Incidents ────────────────────────────────────────────────────────────────

@router.get(
    "/incidents",
    response_model=IncidentListResponse,
    summary="List aggregated incidents",
    tags=["Incidents"],
)
async def list_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    date_start: Optional[datetime] = Query(None, description="Filter by start date"),
    date_end: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    incidents, total = crud.list_incidents(
        db, page=page, limit=limit, status=status, severity=severity, date_start=date_start, date_end=date_end
    )
    return {"total": total, "incidents": incidents}


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
    tags=["Incidents"],
)
async def create_incident(
    payload: IncidentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    return crud.create_incident(db, payload.model_dump())


# ─── Threat Intelligence ──────────────────────────────────────────────────────

@router.get(
    "/threat-intel",
    response_model=ThreatIntelListResponse,
    summary="List cached threat intelligence indicators",
    tags=["Threat Intelligence"],
)
async def list_threat_intel(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    threats, total = crud.list_threat_intel(db, page=page, limit=limit)
    return {"total": total, "threats": threats}

# ─── Settings / Integrations ──────────────────────────────────────────────────

def _mask_secret(value: str) -> str:
    if not value or value == "MOCK":
        return "MOCK"
    if len(value) <= 8:
        return value
    return f"{value[:4]}...{value[-4:]}"


@router.get(
    "/settings",
    response_model=SettingsResponse,
    summary="Get UI settings",
    tags=["Settings"],
)
async def get_settings(current_user: User = Depends(get_current_user_or_api_key)):
    return get_system_settings()


@router.put(
    "/settings",
    response_model=SettingsResponse,
    summary="Update UI settings",
    tags=["Settings"],
)
async def update_settings(
    payload: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user_or_api_key),
):
    patch = payload.model_dump(exclude_unset=True)
    return update_system_settings(patch)


@router.get(
    "/integrations",
    response_model=IntegrationsResponse,
    summary="Get integrations status",
    tags=["Settings"],
)
async def get_integrations(current_user: User = Depends(get_current_user_or_api_key)):
    threat_intel_connected = not (
        app_settings.is_mock("VIRUSTOTAL_API_KEY")
        and app_settings.is_mock("ABUSEIPDB_API_KEY")
        and app_settings.is_mock("OTX_API_KEY")
    )
    return {
        "integrations": [
            {
                "name": "SIEM Integration",
                "description": "Connect to your SIEM platform",
                "status": "Not Connected",
                "status_detail": "No SIEM connector configured",
            },
            {
                "name": "Email Gateway",
                "description": "Integrate with email security",
                "status": "Not Connected",
                "status_detail": "No email gateway configured",
            },
            {
                "name": "Firewall API",
                "description": "Automate firewall rules",
                "status": "Connected" if app_settings.FIREWALL_ALLOW_EXECUTION else "Not Connected",
                "status_detail": (
                    "Execution enabled" if app_settings.FIREWALL_ALLOW_EXECUTION else "Execution disabled"
                ),
            },
            {
                "name": "Threat Intel Feed",
                "description": "External threat intelligence",
                "status": "Connected" if threat_intel_connected else "Not Connected",
                "status_detail": (
                    "API keys configured" if threat_intel_connected else "API keys not configured"
                ),
            },
        ]
    }


@router.get(
    "/settings/api-keys",
    response_model=ApiKeysResponse,
    summary="List configured API keys (masked)",
    tags=["Settings"],
)
async def get_api_keys(current_user: User = Depends(get_current_user_or_api_key)):
    return {
        "keys": [
            {
                "name": "App API Key",
                "key": _mask_secret(app_settings.API_KEY),
                "status": "Configured",
                "created": "N/A",
                "last_used": "N/A",
            },
            {
                "name": "Slack Webhook",
                "key": _mask_secret(app_settings.SLACK_WEBHOOK_URL),
                "status": "Configured" if not app_settings.is_mock("SLACK_WEBHOOK_URL") else "Mock",
                "created": "N/A",
                "last_used": "N/A",
            },
            {
                "name": "Jira API Token",
                "key": _mask_secret(app_settings.JIRA_API_TOKEN),
                "status": "Configured" if not app_settings.is_mock("JIRA_API_TOKEN") else "Mock",
                "created": "N/A",
                "last_used": "N/A",
            },
            {
                "name": "VirusTotal",
                "key": _mask_secret(app_settings.VIRUSTOTAL_API_KEY),
                "status": "Configured" if not app_settings.is_mock("VIRUSTOTAL_API_KEY") else "Mock",
                "created": "N/A",
                "last_used": "N/A",
            },
            {
                "name": "AbuseIPDB",
                "key": _mask_secret(app_settings.ABUSEIPDB_API_KEY),
                "status": "Configured" if not app_settings.is_mock("ABUSEIPDB_API_KEY") else "Mock",
                "created": "N/A",
                "last_used": "N/A",
            },
            {
                "name": "OTX",
                "key": _mask_secret(app_settings.OTX_API_KEY),
                "status": "Configured" if not app_settings.is_mock("OTX_API_KEY") else "Mock",
                "created": "N/A",
                "last_used": "N/A",
            },
        ]
    }


# ─── User Management ──────────────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List users",
    tags=["Users"],
)
async def list_users_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    if current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return crud.list_users(db)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    tags=["Users"],
)
async def create_user_endpoint(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    if current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    existing = crud.get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    password_hash = get_password_hash(payload.password)
    return crud.create_user(db, payload.username, payload.email, password_hash, payload.role)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update an existing user",
    tags=["Users"],
)
async def update_user_endpoint(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    if current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = get_password_hash(data.pop("password"))

    user = crud.update_user(db, user_id, **data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# ─── WebSockets ───────────────────────────────────────────────────────────────

from fastapi import WebSocket, WebSocketDisconnect
from app.core.websockets import manager

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect the client to send messages, just listen.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

from __future__ import annotations

import uuid
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import Alert, EnrichmentResult, ActionLog, Playbook, User, Incident, ThreatIndicator


# ─── Alert Operations ─────────────────────────────────────────────────────────

def create_alert(
    db: Session,
    source_integration: str,
    raw_data: dict,
    external_id: Optional[str] = None,
) -> Alert:
    alert = Alert(
        source_integration=source_integration,
        raw_data=raw_data,
        external_id=external_id,
        status="New",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alert(db: Session, alert_id: str) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def list_alerts(
    db: Session,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    date_start: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
) -> tuple[List[Alert], int]:
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if date_start:
        query = query.filter(Alert.created_at >= date_start)
    if date_end:
        query = query.filter(Alert.created_at <= date_end)
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return alerts, total


def update_alert_status(db: Session, alert_id: str, status: str) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if alert:
        alert.status = status
        db.commit()
        db.refresh(alert)
    return alert


def update_alert_normalized_data(db: Session, alert_id: str, normalized_data: dict) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if alert:
        alert.normalized_data = normalized_data
        db.commit()
        db.refresh(alert)
    return alert


def update_alert_risk(db: Session, alert_id: str, risk_score: int, severity: str) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if alert:
        alert.risk_score = risk_score
        alert.severity = severity
        db.commit()
        db.refresh(alert)
    return alert


# ─── Enrichment Operations ────────────────────────────────────────────────────

def create_enrichment_result(
    db: Session,
    alert_id: str,
    observable_type: str,
    observable_value: str,
    source_provider: str,
    result_data: dict,
    reputation_score: float,
) -> EnrichmentResult:
    record = EnrichmentResult(
        alert_id=alert_id,
        observable_type=observable_type,
        observable_value=observable_value,
        source_provider=source_provider,
        result_data=result_data,
        reputation_score=reputation_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_enrichment_results(db: Session, alert_id: str) -> List[EnrichmentResult]:
    return db.query(EnrichmentResult).filter(EnrichmentResult.alert_id == alert_id).all()


# ─── Action Log Operations ────────────────────────────────────────────────────

def create_action_log(
    db: Session,
    alert_id: str,
    action_name: str,
    status: str,
    output_log: Optional[str] = None,
    playbook_id: Optional[str] = None,
    executed_by: str = "system",
) -> ActionLog:
    log = ActionLog(
        alert_id=alert_id,
        action_name=action_name,
        status=status,
        output_log=output_log,
        playbook_id=playbook_id,
        executed_by=executed_by,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_action_logs(db: Session, alert_id: str) -> List[ActionLog]:
    return db.query(ActionLog).filter(ActionLog.alert_id == alert_id).all()


# ─── Metrics ──────────────────────────────────────────────────────────────────

def get_metrics(db: Session) -> dict:
    from sqlalchemy import func
    total = db.query(func.count(Alert.id)).scalar()
    by_status = db.query(Alert.status, func.count(Alert.id)).group_by(Alert.status).all()
    by_severity = db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all()
    avg_score = db.query(func.avg(Alert.risk_score)).scalar()
    return {
        "total_alerts": total,
        "by_status": {s: c for s, c in by_status},
        "by_severity": {s: c for s, c in by_severity if s},
        "average_risk_score": round(float(avg_score or 0), 2),
    }

# ─── Playbook Operations ──────────────────────────────────────────────────────

def get_playbooks(db: Session, include_inactive: bool = False) -> List[Playbook]:
    query = db.query(Playbook)
    if not include_inactive:
        query = query.filter(Playbook.is_active == True)
    return query.order_by(Playbook.created_at.desc()).all()


def toggle_playbook(db: Session, playbook_id: str, is_active: bool) -> Optional[Playbook]:
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if playbook:
        playbook.is_active = is_active
        db.commit()
        db.refresh(playbook)
    return playbook


def create_playbook(db: Session, playbook_data: dict) -> Playbook:
    db_playbook = Playbook(**playbook_data)
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    return db_playbook

# ─── Incident Operations ──────────────────────────────────────────────────────

def list_incidents(
    db: Session,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    date_start: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
) -> tuple[List[Incident], int]:
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if date_start:
        query = query.filter(Incident.created_at >= date_start)
    if date_end:
        query = query.filter(Incident.created_at <= date_end)
    
    total = query.count()
    incidents = query.order_by(Incident.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # We need to manually calculate total associated alerts for each incident to populate the response
    for inc in incidents:
        inc.alert_count = db.query(func.count(Alert.id)).filter(Alert.incident_id == inc.id).scalar() or 0
        
    return incidents, total


def create_incident(db: Session, payload: dict) -> Incident:
    incident = Incident(
        title=payload["title"],
        description=payload.get("description"),
        severity=payload.get("severity"),
        status=payload.get("status", "Open"),
        assignee=payload.get("assignee"),
        category=payload.get("category"),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

# ─── Threat Intel Operations ──────────────────────────────────────────────────

def list_threat_intel(db: Session, page: int = 1, limit: int = 20) -> tuple[List[ThreatIndicator], int]:
    query = db.query(ThreatIndicator)
    total = query.count()
    threats = query.order_by(ThreatIndicator.last_seen.desc()).offset((page - 1) * limit).limit(limit).all()
    return threats, total

def get_recent_executions(db: Session, limit: int = 50) -> List[dict]:
    results = []
    logs = (
        db.query(ActionLog, Playbook.name, Alert.severity)
        .outerjoin(Playbook, ActionLog.playbook_id == Playbook.id)
        .join(Alert, ActionLog.alert_id == Alert.id)
        .order_by(ActionLog.executed_at.desc())
        .limit(limit)
        .all()
    )
    for log, playbook_name, alert_severity in logs:
        dt_str = log.executed_at.strftime("%b %d, %H:%M") if log.executed_at else "Unknown"
        results.append({
            "id": log.id,
            "playbook": playbook_name or "System Action",
            "action_name": log.action_name,
            "timestamp": dt_str,
            "trigger": f"{alert_severity} Alert" if alert_severity else "Manual",
            "status": log.status,
            "duration": "1.5s", # Mock duration for UI
        })
    return results

def create_playbook(db: Session, playbook_data: dict) -> Playbook:
    db_playbook = Playbook(
        name=playbook_data["name"],
        description=playbook_data.get("description", ""),
        is_active=playbook_data.get("is_active", True),
        trigger_severity=playbook_data["trigger_severity"],
        steps_definition=playbook_data["steps_definition"]
    )
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    return db_playbook

# ─── User Operations ──────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, email: str, password_hash: str, role: str = "admin") -> User:
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> List[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def update_user(db: Session, user_id: str, **fields) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for key, value in fields.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

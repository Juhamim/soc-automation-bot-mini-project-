from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models import Alert, ActionLog, Playbook

def generate_report_data(db: Session, start_time: datetime, end_time: datetime) -> dict:
    """
    Query the database for SOC metrics within the specified time window.
    """
    
    # 1. Total Alerts
    total_alerts = db.query(Alert).filter(
        Alert.created_at >= start_time,
        Alert.created_at <= end_time
    ).count()

    # 2. Alerts by Severity
    severity_counts = dict(
        db.query(Alert.severity, func.count(Alert.id))
        .filter(Alert.created_at >= start_time, Alert.created_at <= end_time)
        .group_by(Alert.severity)
        .all()
    )

    # 3. Alerts by Status
    status_counts = dict(
        db.query(Alert.status, func.count(Alert.id))
        .filter(Alert.created_at >= start_time, Alert.created_at <= end_time)
        .group_by(Alert.status)
        .all()
    )

    # 4. Average Risk Score
    avg_risk = db.query(func.avg(Alert.risk_score)).filter(
        Alert.created_at >= start_time, Alert.created_at <= end_time
    ).scalar() or 0.0

    # 5. Top Triggered Playbooks
    top_playbooks = (
        db.query(Playbook.name, func.count(ActionLog.id))
        .join(ActionLog, ActionLog.playbook_id == Playbook.id)
        .filter(ActionLog.executed_at >= start_time, ActionLog.executed_at <= end_time)
        .group_by(Playbook.name)
        .order_by(func.count(ActionLog.id).desc())
        .limit(5)
        .all()
    )

    return {
        "period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "total_alerts": total_alerts,
        "by_severity": severity_counts,
        "by_status": status_counts,
        "average_risk_score": round(avg_risk, 1),
        "top_playbooks": [{"name": p[0], "count": p[1]} for p in top_playbooks]
    }

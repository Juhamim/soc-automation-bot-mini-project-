import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.database.models import Alert, ActionLog

def check_db():
    db = SessionLocal()
    try:
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(3).all()
        for alert in alerts:
            print(f"Alert ID: {alert.id} | Status: {alert.status} | Source: {alert.source_integration} | Severity: {alert.severity}")
            logs = db.query(ActionLog).filter_by(alert_id=str(alert.id)).all()
            for log in logs:
                print(f"  -> Action: {log.action_name} | Status: {log.status} | Output: {log.output_log}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()

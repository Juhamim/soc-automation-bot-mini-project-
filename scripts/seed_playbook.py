import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import Playbook

def seed_default_playbook():
    db: Session = SessionLocal()
    try:
        existing = db.query(Playbook).filter_by(name="High Severity Threat Response").first()
        if existing:
            print("Playbook already exists.")
            return

        playbook = Playbook(
            name="High Severity Threat Response",
            description="Automatically notifies Slack and blocks the source IP for any Critical alerts with a high malicious score.",
            is_active=True,
            trigger_severity=["High", "Critical"],
            steps_definition={
                "conditions": [
                    {
                        "operator": "AND",
                        "rules": [
                            {"field": "risk_score", "op": ">=", "value": 70},
                            {"field": "enrichment.VirusTotal.reputation_score", "op": ">=", "value": 0.5}
                        ]
                    }
                ],
                "actions": [
                    {
                        "id": "notify_slack",
                        "parameters": {"channel": "#security-alerts"}
                    },
                    {
                        "id": "block_ip",
                        "parameters": {"target": "src_ip"}
                    }
                ]
            }
        )
        db.add(playbook)
        db.commit()
        print("Successfully seeded 'High Severity Threat Response' playbook.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_default_playbook()

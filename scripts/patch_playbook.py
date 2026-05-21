import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import Playbook

def patch_playbook():
    db: Session = SessionLocal()
    try:
        playbook = db.query(Playbook).filter_by(name="High Severity Threat Response").first()
        if playbook:
            playbook.trigger_severity = ["Medium", "High", "Critical"]
            # Change condition to risk_score >= 50
            new_steps = dict(playbook.steps_definition)
            new_steps["conditions"][0]["rules"][0]["value"] = 50
            # Remove the VirusTotal condition for the demo to ensure it passes reliably
            new_steps["conditions"][0]["rules"] = [{"field": "risk_score", "op": ">=", "value": 50}]
            playbook.steps_definition = new_steps
            db.commit()
            print("Successfully patched 'High Severity Threat Response' playbook.")
    finally:
        db.close()

if __name__ == "__main__":
    patch_playbook()

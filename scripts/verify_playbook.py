import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import Playbook

def verify_playbook():
    db: Session = SessionLocal()
    try:
        playbook = db.query(Playbook).filter_by(name="High Severity Threat Response").first()
        if playbook:
            print(json.dumps(playbook.steps_definition, indent=2))
            print(playbook.trigger_severity)
    finally:
        db.close()

if __name__ == "__main__":
    verify_playbook()

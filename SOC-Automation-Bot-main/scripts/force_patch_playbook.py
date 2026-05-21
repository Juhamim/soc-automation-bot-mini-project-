import sys
import copy
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.database.session import SessionLocal
from app.database.models import Playbook

def force_patch_playbook():
    db: Session = SessionLocal()
    try:
        playbook = db.query(Playbook).filter_by(name="High Severity Threat Response").first()
        if playbook:
            playbook.trigger_severity = ["Medium", "High", "Critical"]
            
            # Deep copy to ensure new dict reference
            new_steps = copy.deepcopy(playbook.steps_definition)
            new_steps["conditions"][0]["rules"] = [{"field": "risk_score", "op": ">=", "value": 50}]
            
            playbook.steps_definition = new_steps
            flag_modified(playbook, "steps_definition")
            flag_modified(playbook, "trigger_severity")
            
            db.commit()
            print("Successfully FORCED patch on 'High Severity Threat Response' playbook.")
    finally:
        db.close()

if __name__ == "__main__":
    force_patch_playbook()

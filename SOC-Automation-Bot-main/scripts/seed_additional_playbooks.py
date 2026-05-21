import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.database.models import Playbook

def seed_playbooks():
    db = SessionLocal()
    try:
        # 1. Suspicious Login
        login_playbook = Playbook(
            name="Suspicious Login Detection & Response",
            description="Automates the detection and response to suspicious login attempts, such as brute-force attacks or logins from malicious IP addresses.",
            is_active=True,
            trigger_severity=["Medium", "High", "Critical"],
            steps_definition={
                "conditions": [
                    {
                        "operator": "AND",
                        "rules": [
                            {"field": "raw_data.failed_attempts", "op": ">", "value": 5}
                        ]
                    }
                ],
                "actions": [
                    {"id": "notify_slack", "name": "notify_slack", "params": {"message": "Suspicious login detected! Please investigate the user account and IP address."}},
                    {"id": "block_ip", "name": "block_ip", "params": {}}
                ]
            }
        )
        
        # 2. Phishing Response
        phishing_playbook = Playbook(
            name="Phishing Response Playbook",
            description="Automates the response to phishing attacks by verifying suspicious emails, blocking malicious URLs, and notifying users.",
            is_active=True,
            trigger_severity=["Medium", "High", "Critical"],
            steps_definition={
                "conditions": [
                    {
                        "operator": "AND",
                        "rules": [
                            {"field": "raw_data.event_type", "op": "==", "value": "phishing"}
                        ]
                    }
                ],
                "actions": [
                    {"id": "notify_slack", "name": "notify_slack", "params": {"message": "Phishing email detected! URL blocked and user notified."}},
                    {"id": "create_jira_ticket", "name": "create_jira_ticket", "params": {"summary": "Phishing Incident Response", "description": "Automated ticket created for phishing email."}}
                ]
            }
        )
        
        # 3. Malware Containment
        malware_playbook = Playbook(
            name="Malware Containment Playbook",
            description="Automates the containment of malware infections by isolating affected systems, blocking malicious processes, and notifying the SOC team.",
            is_active=True,
            trigger_severity=["High", "Critical"],
            steps_definition={
                "conditions": [
                    {
                        "operator": "AND",
                        "rules": [
                            {"field": "severity", "op": "in", "value": ["High", "Critical"]}
                        ]
                    }
                ],
                "actions": [
                    {"id": "isolate_host", "name": "isolate_host", "params": {"dry_run": True}},
                    {"id": "notify_slack", "name": "notify_slack", "params": {"message": "Critical Malware Detected! Initiating automated host separation..."}},
                    {"id": "create_jira_ticket", "name": "create_jira_ticket", "params": {"summary": "Critical Malware Outbreak Containment", "description": "Malware outbreak detected. Host isolation procedure started."}}
                ]
            }
        )
        
        db.add_all([login_playbook, phishing_playbook, malware_playbook])
        db.commit()
        print("Successfully seeded all 3 user-provided playbooks!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding playbooks: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_playbooks()

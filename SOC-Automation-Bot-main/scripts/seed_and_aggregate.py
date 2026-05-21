import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import SessionLocal
from app.database import crud
from app.core.aggregation import aggregate_incidents

def seed_and_aggregate():
    db = SessionLocal()
    
    print("Seeding High-Severity Alerts (Source: CrowdStrike)...")
    for _ in range(4):
        alert = crud.create_alert(
            db,
            source_integration="CrowdStrike Falcon",
            raw_data={"event": "Malware detected on endpoint", "host": "DESKTOP-US-001"}
        )
        crud.update_alert_risk(db, str(alert.id), risk_score=85, severity="Critical")
        
        crud.create_enrichment_result(
            db,
            alert_id=str(alert.id),
            observable_type="ip", observable_value="198.51.100.80",
            source_provider="AbuseIPDB", result_data={"fraud_score": 100},
            reputation_score=0.95
        )

    print("Seeding High-Severity Alerts (Source: Okta)...")
    for _ in range(3):
        alert = crud.create_alert(
            db,
            source_integration="Okta SSO",
            raw_data={"event": "Multiple failed logins", "user": "admin@company.com"}
        )
        crud.update_alert_risk(db, str(alert.id), risk_score=90, severity="High")
        crud.create_enrichment_result(
            db,
            alert_id=str(alert.id),
            observable_type="ip", observable_value="192.0.2.14",
            source_provider="OTX", result_data={"pulse": "Brute Force Campaign"},
            reputation_score=0.8
        )
    
    print("Seeding completed. Running Aggregation Engine...")
    aggregate_incidents()
    print("Aggregation complete!")

if __name__ == "__main__":
    seed_and_aggregate()

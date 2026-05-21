import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import SessionLocal
from app.database.models import Alert, Incident, ThreatIndicator, EnrichmentResult

logger = logging.getLogger(__name__)

def aggregate_incidents():
    """
    Routinely scans recent Alerts and groups them into Incidents based on shared IOCs or sources.
    Also extracts Threat Indicators to populate the Threat Intelligence feed.
    """
    logger.info("Starting incident aggregation cycle...")
    db: Session = SessionLocal()
    
    try:
        # Time window: Look at alerts from the last 24 hours that are not yet assigned to an incident
        recent_threshold = datetime.utcnow() - timedelta(hours=24)
        
        unassigned_alerts = db.query(Alert).filter(
            Alert.incident_id == None,
            Alert.severity.in_(["High", "Critical"]),
            Alert.created_at >= recent_threshold
        ).all()
        
        if not unassigned_alerts:
            logger.info("No unassigned High/Critical alerts to aggregate.")
            return

        # Simple aggregation strategy: Group by source_integration
        # In a real-world scenario, you might group by specific IOCs, identical raw_data fields, MITRE tactics, etc.
        groups = {}
        for alert in unassigned_alerts:
            key = alert.source_integration
            if key not in groups:
                groups[key] = []
            groups[key].append(alert)
            
        for source_key, alerts_in_group in groups.items():
            if len(alerts_in_group) >= 2: # Threshold to create an incident: 2+ related alerts
                # Pick the highest severity in the group
                severity = "Critical" if any(a.severity == "Critical" for a in alerts_in_group) else "High"
                
                # Create a new Incident
                incident = Incident(
                    title=f"Multiple Malicious Activity detected via {source_key}",
                    description=f"Automated aggregation of {len(alerts_in_group)} alerts from {source_key}.",
                    severity=severity,
                    status="Open",
                    category="Aggregated Threat"
                )
                db.add(incident)
                db.flush() # Get the new incident ID
                
                # Assign alerts to this incident
                for alert in alerts_in_group:
                    alert.incident_id = incident.id
                
                logger.info(f"Created Incident {incident.id} with {len(alerts_in_group)} alerts.")
        
        # ─ Populate Threat Indicators from recent EnrichmentResults ─
        recent_enrichments = db.query(EnrichmentResult).filter(
            EnrichmentResult.reputation_score > 0.5,
            EnrichmentResult.queried_at >= recent_threshold
        ).all()
        
        for enrich in recent_enrichments:
            # Check if this indicator already exists
            existing_ti = db.query(ThreatIndicator).filter(
                ThreatIndicator.indicator_value == enrich.observable_value
            ).first()
            
            risk_level = "High" if enrich.reputation_score > 0.8 else "Medium"
            
            if existing_ti:
                existing_ti.occurrences += 1
                existing_ti.last_seen = datetime.utcnow()
                # Upgrade risk if necessary
                if risk_level == "High" and existing_ti.risk_level != "Critical":
                    existing_ti.risk_level = "High"
            else:
                new_ti = ThreatIndicator(
                    indicator_type=enrich.observable_type,
                    indicator_value=enrich.observable_value,
                    risk_level=risk_level,
                    country="Unknown", # You could resolve geo-ip here
                    occurrences=1
                )
                db.add(new_ti)
                db.flush()
                
        db.commit()
    except Exception as e:
        logger.error(f"Error during incident aggregation: {e}")
        db.rollback()
    finally:
        db.close()

from __future__ import annotations

import uuid
import logging
import httpx
import json
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.celery_app import celery_app
from app.database.session import SessionLocal
from app.database import crud
from app.modules.reporting.generator import generate_report_data
from app.modules.reporting.templates import format_slack_report

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.core.tasks.process_alert",
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def process_alert(self, alert_id: str) -> dict:
    """
    Main orchestration task for processing a security alert.
    Pipeline: Normalize → Enrich → Analyze → Respond
    """
    db: Session = SessionLocal()
    try:
        logger.info(f"[Task] Starting processing for alert {alert_id}")

        # ── 1. Fetch alert from DB ─────────────────────────────────────────────
        alert = crud.get_alert(db, alert_id)
        if not alert:
            logger.error(f"[Task] Alert {alert_id} not found in DB")
            return {"status": "error", "message": "Alert not found"}

        crud.update_alert_status(db, alert_id, "InProgress")

        # ── 2. Normalize ───────────────────────────────────────────────────────
        from app.modules.normalization.normalizer import Normalizer
        normalizer = Normalizer()
        normalized_data = normalizer.normalize(alert.raw_data, alert.source_integration)
        crud.update_alert_normalized_data(db, alert_id, normalized_data)
        logger.info(f"[Task] Normalization complete for {alert_id}")

        # ── 3. Extract observables & Enrich ───────────────────────────────────
        from app.modules.enrichment.cache import EnrichmentCache
        from app.modules.enrichment.virustotal import VirusTotalEnricher
        from app.modules.enrichment.abuseipdb import AbuseIPDBEnricher
        from app.modules.enrichment.otx import OTXEnricher

        cache = EnrichmentCache()
        enrichers = [VirusTotalEnricher(), AbuseIPDBEnricher(), OTXEnricher()]

        observables = _extract_observables(normalized_data)
        enrichment_results = []

        for obs_type, obs_value in observables:
            for enricher in enrichers:
                result = cache.get(enricher.provider_name, obs_value)
                if result is None:
                    result = enricher.enrich(obs_type, obs_value)
                    cache.set(enricher.provider_name, obs_value, result)

                enrich_record = crud.create_enrichment_result(
                    db,
                    alert_id=alert_id,
                    observable_type=obs_type,
                    observable_value=obs_value,
                    source_provider=enricher.provider_name,
                    result_data=result,
                    reputation_score=result.get("reputation_score", 0.0),
                )
                enrichment_results.append(result)

        logger.info(f"[Task] Enrichment complete: {len(enrichment_results)} results")

        # ── 4. Risk Scoring ───────────────────────────────────────────────────
        from app.modules.analysis.risk_scorer import RiskScorer
        scorer = RiskScorer()
        risk_score, severity = scorer.calculate(
            normalized_data,
            enrichment_results,
            alert.source_integration,
        )
        crud.update_alert_risk(db, alert_id, risk_score, severity)
        logger.info(f"[Task] Risk score: {risk_score} → Severity: {severity}")

        # ── 5. Execute Playbook ────────────────────────────────────────────────
        from app.modules.analysis.decision_engine import evaluate_playbooks
        from app.modules.response.playbook_engine import PlaybookEngine
        
        actions_to_run = evaluate_playbooks(db, alert)
        
        if actions_to_run:
            engine = PlaybookEngine(db=db, alert_id=alert_id)
            for action in actions_to_run:
                action_id = action.get("id")
                params = action.get("parameters", {})
                params.update({
                    "alert_id": alert_id,
                    "severity": severity,
                    "src_ip": normalized_data.get("src_ip", "unknown"),
                    "event_type": normalized_data.get("event_type", "unknown"),
                    "risk_score": risk_score,
                })
                playbook_id = action.get("playbook_id")
                engine.run_single_action(action_id, params, playbook_id=playbook_id)

        logger.info(f"[Task] Playbook execution complete for {alert_id}, executed {len(actions_to_run)} actions.")

        # ── 6. Finalize ────────────────────────────────────────────────────────
        crud.update_alert_status(db, alert_id, "Closed" if severity in ("Info", "Low") else "InProgress")

        # Broadcast real-time ping to WebSocket clients
        try:
            import redis
            from app.core.websockets import REDIS_URL, ALERTS_CHANNEL
            sync_redis = redis.Redis.from_url(REDIS_URL)
            payload = json.dumps({
                "event": "alert_processed", 
                "alert_id": alert_id, 
                "severity": severity,
                "msg": f"New {severity} threat processed!"
            })
            sync_redis.publish(ALERTS_CHANNEL, payload)
        except Exception as ws_err:
            logger.error(f"[Task] Failed to publish WebSocket event: {ws_err}")

        return {
            "status": "success",
            "alert_id": alert_id,
            "risk_score": risk_score,
            "severity": severity,
        }

    except Exception as exc:
        logger.exception(f"[Task] Processing failed for alert {alert_id}: {exc}")
        crud.update_alert_status(db, alert_id, "New")
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()


def _extract_observables(normalized_data: dict) -> list[tuple[str, str]]:
    """Extract IP addresses, domains, and file hashes from normalized alert data."""
    import re
    observables: list[tuple[str, str]] = []

    ip_fields = ["src_ip", "dest_ip", "source_ip", "destination_ip"]
    for field in ip_fields:
        val = normalized_data.get(field)
        if val and val not in ("unknown", "null", None):
            observables.append(("ip", val))

    domain_fields = ["domain", "hostname", "fqdn"]
    for field in domain_fields:
        val = normalized_data.get(field)
        if val and val not in ("unknown", "null", None):
            observables.append(("domain", val))

    hash_fields = ["file_hash", "md5", "sha256", "sha1"]
    for field in hash_fields:
        val = normalized_data.get(field)
        if val and val not in ("unknown", "null", None):
            observables.append(("hash", val))

    return list(set(observables))  # deduplicate

@celery_app.task(
    bind=True,
    name="app.core.tasks.generate_and_send_report",
    max_retries=3,
    default_retry_delay=5,
)
def generate_and_send_report(self, timeframe: str = "Daily", hours: int = 24) -> dict:
    """
    Background task to generate aggregated SOC metric reports and send them to Slack.
    """
    db: Session = SessionLocal()
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Generate metrics
        report_data = generate_report_data(db, start_time, end_time)

        # Format layout
        slack_blocks = format_slack_report(report_data, timeframe)

        # Send via Webhook
        if settings.is_mock("SLACK_WEBHOOK_URL"):
            logger.info(f"[Reporting] MOCK Slack Report:\n{json.dumps(slack_blocks, indent=2)}")
        else:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    settings.SLACK_WEBHOOK_URL,
                    headers={"Content-Type": "application/json"},
                    content=json.dumps({"blocks": slack_blocks["blocks"], "channel": settings.SLACK_ALERT_CHANNEL}),
                )
                response.raise_for_status()

        logger.info(f"[Reporting] Sent {timeframe} SOC Report to Slack.")
        return {
            "status": "success",
            "timeframe": timeframe,
            "reports_sent": len(channels_list)
        }
        
    except Exception as e:
        logger.error(f"[Task] Report generation failed: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(
    bind=True,
    name="app.core.tasks.run_aggregation",
    max_retries=1,
)
def run_aggregation(self) -> dict:
    """
    Background job to periodically scan Alerts and aggregate them into Incidents and Threat Intel.
    """
    from app.core.aggregation import aggregate_incidents
    try:
        aggregate_incidents()
        return {"status": "success", "message": "Aggregation completed"}
    except Exception as e:
        logger.error(f"[Task] Aggregation failed: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

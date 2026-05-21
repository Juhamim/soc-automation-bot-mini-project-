from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from sqlalchemy.orm import Session

from app.database import crud
from app.modules.response.base import ActionResult
from app.modules.response.firewall import FirewallAction
from app.modules.response.notification import SlackNotificationAction
from app.modules.response.ticketing import JiraTicketAction

logger = logging.getLogger(__name__)

PLAYBOOKS_DIR = Path(__file__).parents[4] / "playbooks"

# Registry of all available actions
ACTION_REGISTRY: Dict[str, Any] = {
    "block_ip": FirewallAction,
    "notify_slack": SlackNotificationAction,
    "create_jira_ticket": JiraTicketAction,
}


class PlaybookEngine:
    """
    Loads YAML playbook definitions, evaluates trigger conditions against
    alert severity, and executes matching steps in sequence.
    Records each action outcome in the action_logs table.
    """

    def __init__(self, db: Session, alert_id: str):
        self.db = db
        self.alert_id = alert_id
        self._playbooks: Optional[List[dict]] = None

    def _load_playbooks(self) -> List[dict]:
        """Load all .yml files from the playbooks directory."""
        if self._playbooks is not None:
            return self._playbooks

        playbooks = []
        if not PLAYBOOKS_DIR.exists():
            logger.warning(f"[PlaybookEngine] Playbooks directory not found: {PLAYBOOKS_DIR}")
            return playbooks

        for pb_file in PLAYBOOKS_DIR.glob("*.yml"):
            try:
                with open(pb_file, "r") as f:
                    pb = yaml.safe_load(f)
                    if pb and pb.get("is_active", True):
                        playbooks.append(pb)
                        logger.debug(f"[PlaybookEngine] Loaded: {pb_file.name}")
            except Exception as e:
                logger.error(f"[PlaybookEngine] Failed to load {pb_file.name}: {e}")

        self._playbooks = playbooks
        return playbooks

    def run(self, severity: str, normalized_data: Dict[str, Any]) -> List[ActionResult]:
        """
        Evaluate all playbooks for the given severity.
        Execute steps for matching playbooks.
        """
        results: List[ActionResult] = []
        playbooks = self._load_playbooks()

        for playbook in playbooks:
            trigger = playbook.get("trigger", {})
            trigger_severities = trigger.get("severity", [])

            if severity not in trigger_severities:
                continue

            logger.info(f"[PlaybookEngine] Triggering playbook: {playbook['name']} (severity={severity})")

            for step in playbook.get("steps", []):
                action_name = step.get("action")
                params = step.get("params", {})

                # Inject context from normalized_data
                params.update({
                    "alert_id": self.alert_id,
                    "severity": severity,
                    "src_ip": normalized_data.get("src_ip", "unknown"),
                    "event_type": normalized_data.get("event_type", "unknown"),
                    "risk_score": normalized_data.get("risk_score", 0),
                })

                result = self.run_single_action(action_name, params)
                results.append(result)

        return results

    def run_single_action(
        self,
        action_name: str,
        params: Dict[str, Any],
        executed_by: str = "system",
        playbook_id: Optional[str] = None,
    ) -> ActionResult:
        """Execute a single named action and persist the result to DB."""
        action_class = ACTION_REGISTRY.get(action_name)

        if not action_class:
            log_msg = f"Unknown action: {action_name}"
            logger.warning(f"[PlaybookEngine] {log_msg}")
            result = ActionResult(
                success=False,
                action_name=action_name,
                output_log=log_msg,
                error=f"Action '{action_name}' not found in registry.",
            )
        else:
            try:
                action_instance = action_class()
                result = action_instance.execute(params)
            except Exception as e:
                logger.exception(f"[PlaybookEngine] Action {action_name} crashed: {e}")
                result = ActionResult(
                    success=False,
                    action_name=action_name,
                    output_log=str(e),
                    error=str(e),
                )

        # Persist to DB
        crud.create_action_log(
            db=self.db,
            alert_id=self.alert_id,
            action_name=action_name,
            status="Success" if result.success else "Failure",
            output_log=result.output_log,
            executed_by=executed_by,
            playbook_id=playbook_id,
        )

        return result

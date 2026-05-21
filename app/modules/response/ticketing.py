from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.modules.response.base import BaseAction, ActionResult

logger = logging.getLogger(__name__)


class JiraTicketAction(BaseAction):
    """
    Creates a Jira issue for a security alert.
    Falls back to mock when JIRA_API_TOKEN=MOCK.
    """

    @property
    def action_name(self) -> str:
        return "create_jira_ticket"

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        alert_id = params.get("alert_id", "N/A")
        severity = params.get("severity", "Medium")
        event_type = params.get("event_type", "Security Incident")
        src_ip = params.get("src_ip", "N/A")
        risk_score = params.get("risk_score", 0)

        issue_data = {
            "fields": {
                "project": {"key": settings.JIRA_PROJECT_KEY},
                "summary": f"[SOC Alert] {severity} - {event_type} from {src_ip}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Automated alert from SOC Bot.\n\n"
                                        f"Alert ID: {alert_id}\n"
                                        f"Severity: {severity}\n"
                                        f"Risk Score: {risk_score}/100\n"
                                        f"Source IP: {src_ip}\n"
                                        f"Event Type: {event_type}"
                                    ),
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
                "priority": {"name": self._severity_to_jira_priority(severity)},
                "labels": ["soc-automation", f"severity-{severity.lower()}"],
            }
        }

        if settings.is_mock("JIRA_API_TOKEN"):
            mock_key = f"{settings.JIRA_PROJECT_KEY}-MOCK-{alert_id[:8].upper()}"
            log_msg = f"[MOCK Jira] Would create issue {mock_key}: {issue_data['fields']['summary']}"
            logger.info(f"[Jira] {log_msg}")
            return ActionResult(
                success=True,
                action_name=self.action_name,
                output_log=log_msg,
                data={"mock": True, "issue_key": mock_key},
            )

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{settings.JIRA_URL}/rest/api/3/issue",
                    auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN),
                    headers={"Content-Type": "application/json"},
                    json=issue_data,
                )
                response.raise_for_status()
                result = response.json()

            issue_key = result.get("key", "UNKNOWN")
            log_msg = f"Jira issue {issue_key} created for alert {alert_id}"
            logger.info(f"[Jira] {log_msg}")
            return ActionResult(
                success=True,
                action_name=self.action_name,
                output_log=log_msg,
                data={"issue_key": issue_key, "issue_url": f"{settings.JIRA_URL}/browse/{issue_key}"},
            )
        except Exception as e:
            logger.error(f"[Jira] Error: {e}")
            return ActionResult(
                success=False,
                action_name=self.action_name,
                output_log=str(e),
                error=str(e),
            )

    def _severity_to_jira_priority(self, severity: str) -> str:
        return {
            "Critical": "Highest",
            "High": "High",
            "Medium": "Medium",
            "Low": "Low",
            "Info": "Lowest",
        }.get(severity, "Medium")

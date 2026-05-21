from __future__ import annotations

import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.modules.response.base import BaseAction, ActionResult

logger = logging.getLogger(__name__)


class SlackNotificationAction(BaseAction):
    """
    Sends a formatted security alert notification to a Slack channel
    via an Incoming Webhook. Falls back to mock logging when SLACK_WEBHOOK_URL=MOCK.
    """

    @property
    def action_name(self) -> str:
        return "notify_slack"

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        alert_id = params.get("alert_id", "N/A")
        severity = params.get("severity", "Unknown")
        risk_score = params.get("risk_score", 0)
        src_ip = params.get("src_ip", "N/A")
        event_type = params.get("event_type", "N/A")
        channel = params.get("channel", settings.SLACK_ALERT_CHANNEL)

        blocks = self._build_slack_blocks(
            alert_id=alert_id,
            severity=severity,
            risk_score=risk_score,
            src_ip=src_ip,
            event_type=event_type,
        )

        if settings.is_mock("SLACK_WEBHOOK_URL"):
            log_msg = f"[MOCK Slack → {channel}] Alert {alert_id} | {severity} | Score: {risk_score} | IP: {src_ip}"
            logger.info(f"[Slack] {log_msg}")
            return ActionResult(
                success=True,
                action_name=self.action_name,
                output_log=log_msg,
                data={"mock": True, "channel": channel, "blocks": blocks},
            )

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    settings.SLACK_WEBHOOK_URL,
                    headers={"Content-Type": "application/json"},
                    content=json.dumps({"blocks": blocks, "channel": channel}),
                )
                response.raise_for_status()

            log_msg = f"Slack notification sent to {channel} for alert {alert_id}"
            logger.info(f"[Slack] {log_msg}")
            return ActionResult(
                success=True,
                action_name=self.action_name,
                output_log=log_msg,
                data={"channel": channel},
            )
        except Exception as e:
            logger.error(f"[Slack] Error: {e}")
            return ActionResult(
                success=False,
                action_name=self.action_name,
                output_log=str(e),
                error=str(e),
            )

    def _severity_emoji(self, severity: str) -> str:
        return {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢",
            "Info": "⚪",
        }.get(severity, "⚫")

    def _build_slack_blocks(
        self,
        alert_id: str,
        severity: str,
        risk_score: int,
        src_ip: str,
        event_type: str,
    ) -> list:
        emoji = self._severity_emoji(severity)
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} SOC Alert — {severity} Severity",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Alert ID:*\n`{alert_id}`"},
                    {"type": "mrkdwn", "text": f"*Risk Score:*\n`{risk_score}/100`"},
                    {"type": "mrkdwn", "text": f"*Event Type:*\n{event_type}"},
                    {"type": "mrkdwn", "text": f"*Source IP:*\n`{src_ip}`"},
                ],
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔍 View Alert"},
                        "url": f"http://localhost:3000/alerts/{alert_id}",
                        "style": "primary",
                    },
                ],
            },
        ]

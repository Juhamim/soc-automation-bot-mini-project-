def format_slack_report(report_data: dict, timeframe_label: str = "Daily") -> dict:
    """
    Formats the raw dictionary report data into a rich Slack Block Kit layout.
    """
    
    total = report_data.get("total_alerts", 0)
    avg_risk = report_data.get("average_risk_score", 0.0)
    sev = report_data.get("by_severity", {})
    status = report_data.get("by_status", {})
    playbooks = report_data.get("top_playbooks", [])

    # Format Severities
    sev_str = "\n".join([f"• *{k}*: {v}" for k, v in sev.items()]) if sev else "No alerts"
    
    # Format Statuses
    stat_str = "\n".join([f"• *{k}*: {v}" for k, v in status.items()]) if status else "No alerts"
    
    # Format Playbooks
    pb_str = "\n".join([f"• {p['name']} ({p['count']} times)" for p in playbooks]) if playbooks else "No automations triggered"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🛡️ SOC Automation {timeframe_label} Report",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Period:* {report_data['period']['start']} to {report_data['period']['end']}\n"
                        f"*Total Alerts Processed:* {total}\n"
                        f"*Average Fleet Risk Score:* {avg_risk}/100"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*By Severity*\n{sev_str}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*By Status*\n{stat_str}"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🤖 Top Triggered Playbooks*\n{pb_str}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Report generated dynamically by the SOC Decision Engine."
                }
            ]
        }
    ]

    return {"blocks": blocks}

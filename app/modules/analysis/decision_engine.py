import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Alert, Playbook

logger = logging.getLogger(__name__)

def get_nested_value(d: Dict[str, Any], path: str) -> Any:
    """Retrieve a nested value from a dictionary using dot notation."""
    keys = path.split('.')
    val = d
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return None
    return val

def evaluate_condition(rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
    field = rule.get("field")
    op = rule.get("op")
    target_value = rule.get("value")

    actual_value = get_nested_value(context, field) if field else None

    if actual_value is None:
        logger.debug(f"Field {field} not found in context.")
        return False

    try:
        if op == "==":
            return actual_value == target_value
        elif op == "!=":
            return actual_value != target_value
        elif op == ">=":
            return float(actual_value) >= float(target_value)
        elif op == "<=":
            return float(actual_value) <= float(target_value)
        elif op == ">":
            return float(actual_value) > float(target_value)
        elif op == "<":
            return float(actual_value) < float(target_value)
        elif op == "in":
            return actual_value in target_value
        elif op == "contains":
            return target_value in actual_value
        else:
            logger.warning(f"Unknown operator: {op}")
            return False
    except (ValueError, TypeError) as e:
        logger.warning(f"Error evaluating condition {field} {op} {target_value}: {e}")
        return False

def evaluate_rule_group(group: Dict[str, Any], context: Dict[str, Any]) -> bool:
    operator = group.get("operator", "AND").upper()
    rules = group.get("rules", [])
    
    if not rules:
        return True

    results = []
    for rule in rules:
        # Check if it's a nested group
        if "rules" in rule:
            results.append(evaluate_rule_group(rule, context))
        else:
            results.append(evaluate_condition(rule, context))
            
    if operator == "AND":
        return all(results)
    elif operator == "OR":
        return any(results)
    else:
        logger.warning(f"Unknown logical operator: {operator}")
        return False

def build_alert_context(alert: Alert) -> Dict[str, Any]:
    """Build a context dictionary from the alert for condition evaluation."""
    context = {
        "source": alert.source_integration,
        "risk_score": alert.risk_score or 0,
        "severity": alert.severity,
        "status": alert.status,
        "raw_data": alert.raw_data or {},
        "normalized_data": alert.normalized_data or {},
        "enrichment": {}
    }
    
    # Add enrichment results to context
    # e.g. enrichment.VirusTotal.malicious
    if hasattr(alert, "enrichment_results") and alert.enrichment_results:
        for er in alert.enrichment_results:
            provider = er.source_provider
            if provider not in context["enrichment"]:
                context["enrichment"][provider] = {}
            if er.result_data:
                context["enrichment"][provider].update(er.result_data)
                
    return context

def evaluate_playbooks(db: Session, alert: Alert) -> List[Dict[str, Any]]:
    """
    Evaluates an alert against all active playbooks and returns a list of actions to execute.
    """
    actions_to_execute = []
    
    # Fetch active playbooks
    playbooks = db.query(Playbook).filter(Playbook.is_active == True).all()
    if not playbooks:
        logger.info("No active playbooks found.")
        return actions_to_execute

    context = build_alert_context(alert)
    logger.debug(f"Alert Context for Playbook Evaluation: {context}")

    for playbook in playbooks:
        logger.info(f"Evaluating Playbook '{playbook.name}'...")
        
        # Check trigger severity first (fast fail)
        if playbook.trigger_severity and alert.severity not in playbook.trigger_severity:
            logger.debug(f"Playbook '{playbook.name}' failed trigger severity check.")
            continue
            
        steps = playbook.steps_definition
        if not steps:
            logger.debug(f"Playbook '{playbook.name}' has no defined steps.")
            continue
            
        conditions = steps.get("conditions", [])
        playbook_matched = True
        
        # If there are conditions, evaluate them (AND logic between top-level groups)
        if conditions:
            group_results = []
            for group in conditions:
                group_results.append(evaluate_rule_group(group, context))
            playbook_matched = all(group_results)
            
        if playbook_matched:
            logger.info(f"Playbook '{playbook.name}' matched! Queuing actions.")
            actions = steps.get("actions", [])
            for action in actions:
                # Inject playbook_id so we can log it later
                action_copy = dict(action)
                action_copy["playbook_id"] = str(playbook.id)
                actions_to_execute.append(action_copy)

    return actions_to_execute

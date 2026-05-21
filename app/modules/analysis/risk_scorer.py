from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

# Severity label → base score range midpoint
SEVERITY_BASE_SCORES: Dict[str, int] = {
    "Info": 10,
    "Low": 30,
    "Medium": 55,
    "High": 80,
    "Critical": 95,
}


class RiskScorer:
    """
    Calculates a composite risk score (0–100) from:
        - Source severity (40% weight)
        - Threat intel reputation average (40% weight)
        - Alert recurrence stub (20% weight — placeholder for Phase 2+)
    Maps score → severity label using PRD thresholds.
    """

    def calculate(
        self,
        normalized_data: Dict[str, Any],
        enrichment_results: List[Dict[str, Any]],
        source_integration: str,
    ) -> Tuple[int, str]:
        """
        Returns: (risk_score: int, severity_label: str)
        """

        # ── Component 1: Source Severity Score (40%) ──────────────────────────
        src_severity = normalized_data.get("severity", "Low")
        base_score = SEVERITY_BASE_SCORES.get(src_severity, 30)
        severity_component = base_score * 0.40

        # ── Component 2: Threat Intel Reputation (40%) ────────────────────────
        tip_scores = [r.get("reputation_score", 0.0) for r in enrichment_results if "reputation_score" in r]
        avg_tip_score = (sum(tip_scores) / len(tip_scores)) if tip_scores else 0.0
        tip_component = avg_tip_score * 100 * 0.40

        # ── Component 3: Recurrence / Context (20%) ───────────────────────────
        # Placeholder: gives 100/100 points by default (can be enhanced later)
        recurrence_component = 100 * 0.20

        # ── Aggregate ─────────────────────────────────────────────────────────
        raw_score = severity_component + tip_component + recurrence_component
        risk_score = min(100, max(0, int(round(raw_score))))

        # When no TIP data, trust source severity for the label
        if not enrichment_results:
            severity_label = normalized_data.get("severity", "Low")
        else:
            severity_label = self._score_to_severity(risk_score)

        logger.info(
            f"[RiskScorer] base={base_score} tip_avg={avg_tip_score:.2f} "
            f"→ score={risk_score} ({severity_label})"
        )

        return risk_score, severity_label

    def _score_to_severity(self, score: int) -> str:
        cfg = settings
        if score < cfg.RISK_SCORE_LOW_THRESHOLD:
            return "Info"
        elif score < cfg.RISK_SCORE_MEDIUM_THRESHOLD:
            return "Low"
        elif score < cfg.RISK_SCORE_HIGH_THRESHOLD:
            return "Medium"
        elif score < cfg.RISK_SCORE_CRITICAL_THRESHOLD:
            return "High"
        else:
            return "Critical"

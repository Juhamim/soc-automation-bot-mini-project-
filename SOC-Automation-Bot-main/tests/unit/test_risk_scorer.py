import pytest
from app.modules.analysis.risk_scorer import RiskScorer


def test_info_severity_low_score():
    scorer = RiskScorer()
    score, severity = scorer.calculate(
        {"severity": "Info"},
        [],
        "Wazuh"
    )
    assert 0 <= score <= 30
    assert severity in ("Info", "Low")


def test_critical_severity_high_score():
    scorer = RiskScorer()
    score, severity = scorer.calculate(
        {"severity": "Critical"},
        [{"reputation_score": 0.9}, {"reputation_score": 0.85}],
        "Splunk"
    )
    assert score >= 70
    assert severity in ("High", "Critical")


def test_no_enrichment_uses_source_severity():
    scorer = RiskScorer()
    score, severity = scorer.calculate(
        {"severity": "High"},
        [],  # No TIP data
        "Generic"
    )
    assert score >= 30
    assert severity in ("Medium", "High", "Critical")


def test_score_capped_at_100():
    scorer = RiskScorer()
    score, _ = scorer.calculate(
        {"severity": "Critical"},
        [{"reputation_score": 1.0}] * 10,
        "Wazuh"
    )
    assert score <= 100


def test_score_floored_at_0():
    scorer = RiskScorer()
    score, _ = scorer.calculate(
        {"severity": "Info"},
        [{"reputation_score": 0.0}],
        "Wazuh"
    )
    assert score >= 0


def test_returns_tuple():
    scorer = RiskScorer()
    result = scorer.calculate({"severity": "Medium"}, [], "Wazuh")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], int)
    assert isinstance(result[1], str)

import pytest
from app.modules.normalization.normalizer import Normalizer


normalizer = Normalizer()


def test_wazuh_src_ip_mapping():
    raw = {"data": {"srcip": "192.168.1.1"}, "source": "Wazuh"}
    result = normalizer.normalize(raw, "Wazuh")
    assert result["src_ip"] == "192.168.1.1"


def test_generic_src_ip_mapping():
    raw = {"src_ip": "10.0.0.1"}
    result = normalizer.normalize(raw, "Generic")
    assert result["src_ip"] == "10.0.0.1"


def test_missing_fields_default_to_unknown():
    raw = {"source": "Test"}
    result = normalizer.normalize(raw, "Test")
    assert result["src_ip"] == "unknown"
    assert result["severity"] == "unknown"


def test_severity_normalization_wazuh_level():
    raw = {"rule.level": "10"}
    result = normalizer.normalize(raw, "Wazuh")
    assert result["severity"] == "High"


def test_severity_normalization_generic():
    raw = {"severity": "critical"}
    result = normalizer.normalize(raw, "Splunk")
    assert result["severity"] == "Critical"


def test_source_integration_preserved():
    raw = {}
    result = normalizer.normalize(raw, "MyTool")
    assert result["source_integration"] == "MyTool"


def test_nested_flattening():
    raw = {"agent": {"name": "server01"}}
    result = normalizer.normalize(raw, "Wazuh")
    assert result["hostname"] == "server01"

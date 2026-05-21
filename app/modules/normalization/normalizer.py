from __future__ import annotations

from typing import Any, Dict


class Normalizer:
    """
    Maps vendor-specific alert fields to a standardized internal schema.
    Supports Wazuh, Splunk, and Generic webhook formats.
    """

    # Vendor field aliases → standard field name
    FIELD_MAP = {
        # Source IP
        "src_ip": "src_ip",
        "source_ip": "src_ip",
        "sourceAddress": "src_ip",
        "src": "src_ip",
        "attacker_ip": "src_ip",
        "data.srcip": "src_ip",
        # Destination IP
        "dest_ip": "dest_ip",
        "destination_ip": "dest_ip",
        "destinationAddress": "dest_ip",
        "dst": "dest_ip",
        "data.dstip": "dest_ip",
        # Event type
        "event_type": "event_type",
        "rule.description": "event_type",
        "eventtype": "event_type",
        "signature": "event_type",
        # Severity
        "severity": "severity",
        "rule.level": "severity",
        "urgency": "severity",
        "priority": "severity",
        # Username
        "username": "username",
        "user": "username",
        "data.dstuser": "username",
        # Hostname
        "hostname": "hostname",
        "host": "hostname",
        "agent.name": "hostname",
        "computer": "hostname",
        # Domain
        "domain": "domain",
        "fqdn": "domain",
        "data.hostname": "domain",
        # File hash
        "file_hash": "file_hash",
        "md5": "file_hash",
        "sha256": "file_hash",
        "sha1": "file_hash",
        "data.md5": "file_hash",
        # Source
        "source": "source_integration",
    }

    SEVERITY_MAP = {
        # Wazuh levels (0-15)
        "1": "Info", "2": "Info", "3": "Info",
        "4": "Low", "5": "Low", "6": "Low",
        "7": "Medium", "8": "Medium", "9": "Medium",
        "10": "High", "11": "High", "12": "High",
        "13": "Critical", "14": "Critical", "15": "Critical",
        # Splunk / generic
        "informational": "Info", "info": "Info",
        "low": "Low",
        "medium": "Medium", "moderate": "Medium",
        "high": "High",
        "critical": "Critical", "severe": "Critical",
    }

    def normalize(self, raw_data: dict, source_integration: str) -> dict:
        """
        Flatten and normalize a raw alert payload.
        Returns a standardized dict with all known fields.
        """
        flat = self._flatten(raw_data)
        normalized: Dict[str, Any] = {}

        # Map fields
        for raw_key, std_key in self.FIELD_MAP.items():
            if raw_key in flat:
                normalized[std_key] = flat[raw_key]

        # Normalize severity label
        sev = normalized.get("severity")
        if sev:
            normalized["severity"] = self.SEVERITY_MAP.get(str(sev).lower(), str(sev).capitalize())

        # Fill defaults
        defaults = {k: "unknown" for k in [
            "src_ip", "dest_ip", "event_type", "severity",
            "username", "hostname", "domain", "file_hash",
        ]}
        for key, default in defaults.items():
            if key not in normalized or not normalized[key]:
                normalized[key] = default

        normalized["source_integration"] = source_integration
        return normalized

    def _flatten(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Flatten nested dicts (e.g. Wazuh's {'data': {'srcip': '1.2.3.4'}})."""
        items: Dict[str, Any] = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten(v, new_key, sep=sep))
            else:
                items[new_key] = v
                items[k] = v  # Also keep non-dotted key for convenience
        return items

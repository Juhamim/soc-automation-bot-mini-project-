from __future__ import annotations

import logging
import subprocess
import platform
import ipaddress
from typing import Any, Dict

from app.modules.response.base import BaseAction, ActionResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class FirewallAction(BaseAction):
    """
    Blocks an IP address using Windows Defender Firewall (Windows) or iptables (Linux).
    In development/mock mode, it logs the command without executing it.
    """

    @property
    def action_name(self) -> str:
        return "block_ip"

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        ip_address = params.get("ip_address") or params.get("src_ip")
        target_key = params.get("target")
        if not ip_address and isinstance(target_key, str):
            ip_address = params.get(target_key)
        chain = params.get("chain", "INPUT")  # Only relevant for iptables
        simulate = params.get("simulate", True)  # Default: simulate in dev

        if not ip_address or ip_address == "unknown":
            return ActionResult(
                success=False,
                action_name=self.action_name,
                output_log="No IP address provided for blocking.",
                error="Missing parameter: ip_address",
            )

        try:
            ipaddress.ip_address(str(ip_address))
        except ValueError:
            return ActionResult(
                success=False,
                action_name=self.action_name,
                output_log=f"Invalid IP address: {ip_address}",
                error="Invalid IP address",
            )

        os_type = platform.system().lower()
        if os_type == "windows":
            # Windows Defender Firewall Rule
            command = f'netsh advfirewall firewall add rule name="SOC Block {ip_address}" dir=in action=block remoteip={ip_address}'
            tool = "Windows Defender"
        else:
            # Linux iptables fallback
            command = f"iptables -A {chain} -s {ip_address} -j DROP"
            tool = "iptables"

        if simulate:
            log_msg = f"[{tool}] [SIMULATED] Would execute: {command}"
            logger.info(f"[Firewall] {log_msg}")
            return ActionResult(
                success=True,
                action_name=self.action_name,
                output_log=log_msg,
                data={"ip_address": ip_address, "tool": tool, "simulated": True},
            )

        if not settings.FIREWALL_ALLOW_EXECUTION:
            log_msg = f"[{tool}] Execution blocked by FIREWALL_ALLOW_EXECUTION=false"
            logger.warning(f"[Firewall] {log_msg}")
            return ActionResult(
                success=False,
                action_name=self.action_name,
                output_log=log_msg,
                error="Firewall execution disabled by config",
            )

        # Real execution (Requires Administrator/Root privileges)
        try:
            # Need shell=True for netsh quotes to parse correctly sometimes,
            # but splitting works if careful. For safety with standard libraries we use shell on Windows:
            result = subprocess.run(
                command if os_type == "windows" else command.split(),
                shell=(os_type == "windows"),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                log_msg = f"Successfully blocked IP {ip_address} via {tool}"
                logger.info(f"[Firewall] {log_msg}")
                return ActionResult(
                    success=True,
                    action_name=self.action_name,
                    output_log=log_msg,
                    data={"ip_address": ip_address, "tool": tool, "simulated": False},
                )
            else:
                logger.error(f"[Firewall] {tool} failed: {result.stderr or result.stdout}")
                return ActionResult(
                    success=False,
                    action_name=self.action_name,
                    output_log=result.stderr or result.stdout,
                    error=result.stderr or result.stdout,
                )
        except Exception as e:
            logger.exception(f"[Firewall] Exception: {e}")
            return ActionResult(
                success=False,
                action_name=self.action_name,
                output_log=str(e),
                error=str(e),
            )

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ActionResult:
    """Standardized result object returned by every action executor."""
    success: bool
    action_name: str
    output_log: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAction(ABC):
    """
    Abstract base class for all response actions (firewall, slack, jira, etc.)
    """

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Unique action identifier used in playbooks."""
        ...

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ActionResult:
        """
        Execute the action with the given parameters.
        Must return an ActionResult regardless of success/failure.
        """
        ...

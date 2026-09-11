from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.ai.models import AgentAuditContext, AgentResult


class AgentGraph(ABC):
    """Base interface for all LangGraph graph implementations."""

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the graph with input data and return result."""
        ...

    def configure_audit(self, context: AgentAuditContext) -> None:
        self.audit_context = context

    @property
    @abstractmethod
    def name(self) -> str: ...

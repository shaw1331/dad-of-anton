from __future__ import annotations

from abc import ABC, abstractmethod


class AnalysisStrategy(ABC):
    """Domain-specific analysis strategy (prompts)."""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this strategy."""
        ...

    @abstractmethod
    def get_analysis_prompt(self, stock_data: dict) -> str:
        """Return the analysis prompt for a specific stock."""
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...

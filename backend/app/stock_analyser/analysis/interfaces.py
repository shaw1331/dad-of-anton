from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.stock_analyser.formatters import StockDataFormatorFactory
from app.stock_analyser.formatters.base import BaseStockFormatter


class AnalysisStrategy(ABC):
    """Domain-specific analysis strategy (prompts)."""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this strategy."""
        ...

    @abstractmethod
    def get_analysis_prompt(self, stock_data: dict, analyzed_news: list[dict] | None = None) -> str:
        """Return the analysis prompt for a specific stock."""
        ...

    @abstractmethod
    def get_output_model(self) -> type[BaseModel]:
        """Return the Pydantic model for structured LLM output."""
        ...

    def get_formatter(self) -> BaseStockFormatter:
        """Return the formatter used to structure stock data for this strategy."""
        return StockDataFormatorFactory.get(type(self))

    @property
    @abstractmethod
    def name(self) -> str: ...

from __future__ import annotations

from typing import Type

from app.scraper.exceptions import ConfigError
from app.stock_analyser.analysis.interfaces import AnalysisStrategy


class AnalysisFactory:
    """Factory for creating analysis strategy instances.

    Strategies are registered by name (e.g., "value_investing", "momentum").
    Use get() to retrieve an instance.
    """

    _strategies: dict[str, Type[AnalysisStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_cls: Type[AnalysisStrategy]) -> None:
        """Register an AnalysisStrategy implementation."""
        cls._strategies[name] = strategy_cls

    @classmethod
    def get(cls, name: str = "value_investing") -> AnalysisStrategy:
        """Get an AnalysisStrategy instance by name.

        Args:
            name: The registered strategy name.

        Returns:
            An AnalysisStrategy instance.

        Raises:
            ConfigError: If no strategy is registered for the name.
        """
        strategy_cls = cls._strategies.get(name)
        if strategy_cls is None:
            available = list(cls._strategies.keys())
            raise ConfigError(
                f"No AnalysisStrategy registered for '{name}'. "
                f"Available strategies: {available}"
            )
        return strategy_cls()

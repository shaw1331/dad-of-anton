from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.stock_analyser.analysis.interfaces import AnalysisStrategy
    from app.stock_analyser.formatters.base import BaseStockFormatter


class StockDataFormatorFactory:
    """Factory for creating stock data formatters based on analysis strategy."""

    _registry: dict[type[AnalysisStrategy], type[BaseStockFormatter]] = {}
    _imported = False

    @classmethod
    def _ensure_imports(cls) -> None:
        if cls._imported:
            return
        cls._imported = True
        from app.stock_analyser.formatters import momentum_formatter  # noqa: F401
        from app.stock_analyser.formatters import value_formatter  # noqa: F401

    @classmethod
    def register(cls, strategy_cls: type[AnalysisStrategy], formatter_cls: type[BaseStockFormatter]) -> None:
        cls._registry[strategy_cls] = formatter_cls

    @classmethod
    def get(cls, strategy_cls: type[AnalysisStrategy]) -> BaseStockFormatter:
        cls._ensure_imports()
        formatter_cls = cls._registry.get(strategy_cls)
        if formatter_cls is None:
            available = [s.__name__ for s in cls._registry.keys()]
            raise ValueError(
                f"No formatter registered for '{strategy_cls.__name__}'. "
                f"Available: {available}"
            )
        return formatter_cls()

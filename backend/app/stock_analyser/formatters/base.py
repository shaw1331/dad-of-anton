from __future__ import annotations

from abc import ABC, abstractmethod


class BaseStockFormatter(ABC):
    """Base class for strategy-specific stock data formatters."""

    @abstractmethod
    def format(self, stock_data: dict, analyzed_news: list[dict], meta: dict) -> str:
        """Format stock data and news into a structured Markdown prompt.

        Args:
            stock_data: Raw stock data dict from ScrapeStocksTask.
            analyzed_news: List of analyzed news dicts from AnalyzeNewsTask.
            meta: Metadata dict with keys: ticker, company_name, sector, industry.

        Returns:
            Structured Markdown string for the LLM.
        """
        ...

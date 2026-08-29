from __future__ import annotations

from abc import ABC, abstractmethod

from app.scraper.models import ScraperResult, StockDTO, StockSummaryDTO


class IndexScraper(ABC):
    @abstractmethod
    def get_stocks(self, index_name: str) -> ScraperResult[list[StockSummaryDTO]]:
        """Scrape all stocks from an index.

        Args:
            index_name: Name of the index to scrape (e.g., "NIFTY50", "SMALLCAP50").

        Returns:
            ScraperResult containing a list of StockSummaryDTO on success.
        """
        ...


class StockScraper(ABC):
    @abstractmethod
    def get_technical_data(self, ticker: str) -> ScraperResult[StockDTO]:
        """Scrape technical data for a single stock.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE", "TCS").

        Returns:
            ScraperResult containing a StockDTO on success.
        """
        ...

    @abstractmethod
    def get_multiple(self, tickers: list[str]) -> ScraperResult[list[StockDTO]]:
        """Scrape technical data for multiple stocks.

        Args:
            tickers: List of stock ticker symbols.

        Returns:
            ScraperResult containing a list of StockDTO on success.
            Individual stock failures are handled gracefully.
        """
        ...

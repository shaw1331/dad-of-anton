from __future__ import annotations

import logging
import time

from app.scraper.interfaces import StockScraper
from app.scraper.models import ScraperResult, StockDTO
from app.scraper.trendlyne_scraper.config import (
    BASE_URL,
    REQUEST_DELAY,
    SEARCH_API,
    TECHNICAL_API,
)
from app.scraper.trendlyne_scraper.http import get_json, get_page
from app.scraper.trendlyne_scraper.mappers import map_search_result, map_technicals

logger = logging.getLogger(__name__)


class TrendlyneStockScraper(StockScraper):
    """StockScraper implementation for trendlyne.com."""

    def _resolve_stock_id(self, ticker: str) -> str | None:
        """Search Trendlyne for a ticker and return its stock_id."""
        url = f"{BASE_URL}{SEARCH_API}"
        params = {"term": ticker, "all-results": "true"}
        data = get_json(url, params=params)
        if not data:
            return None
        return map_search_result(data)

    def get_technical_data(self, ticker: str) -> ScraperResult[StockDTO]:
        """Fetch technical indicator data for a single stock from Trendlyne.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE", "TCS").

        Returns:
            ScraperResult containing a StockDTO with technical data.
        """
        stock_id = self._resolve_stock_id(ticker)
        if not stock_id:
            return ScraperResult(
                success=False,
                error=f"No Trendlyne stock found for ticker '{ticker}'",
                source="trendlyne",
            )

        url = f"{BASE_URL}{TECHNICAL_API.format(stock_id=stock_id)}"
        soup = get_page(url)
        if not soup:
            return ScraperResult(
                success=False,
                error=f"Failed to fetch technical data for ticker '{ticker}'",
                source="trendlyne",
            )

        html_str = str(soup)
        technical_url = f"{BASE_URL}/equity/{stock_id}/{ticker}/"
        stock_dto = map_technicals(html_str, ticker, technical_url)

        return ScraperResult(
            success=True,
            data=stock_dto,
            source="trendlyne",
        )

    def get_multiple(self, tickers: list[str]) -> ScraperResult[list[StockDTO]]:
        """Fetch technical data for multiple stocks with rate limiting.

        Args:
            tickers: List of stock ticker symbols.

        Returns:
            ScraperResult containing a list of StockDTOs.
            Individual failures are skipped gracefully.
        """
        results: list[StockDTO] = []

        for i, ticker in enumerate(tickers):
            result = self.get_technical_data(ticker)
            if result.success and result.data:
                results.append(result.data)
                logger.info("Scraped %s (%d/%d)", ticker, i + 1, len(tickers))
            else:
                logger.warning("Failed to scrape %s: %s", ticker, result.error)

            if i < len(tickers) - 1:
                time.sleep(REQUEST_DELAY)

        return ScraperResult(
            success=True,
            data=results,
            source="trendlyne",
        )

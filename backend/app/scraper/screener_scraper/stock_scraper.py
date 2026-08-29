from __future__ import annotations

import logging
import time

from app.scraper.interfaces import StockScraper
from app.scraper.models import ScraperResult, StockDTO
from app.scraper.screener_scraper.config import REQUEST_DELAY
from app.scraper.screener_scraper.http import get_page
from app.scraper.screener_scraper.mappers import map_company_page

logger = logging.getLogger(__name__)


class ScreenerStockScraper(StockScraper):
    """StockScraper implementation for screener.in."""

    def get_technical_data(self, ticker: str) -> ScraperResult[StockDTO]:
        """Scrape technical data for a single stock.

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE").

        Returns:
            ScraperResult containing a StockDTO on success.
        """
        from app.scraper.screener_scraper.config import BASE_URL

        url = f"{BASE_URL}/company/{ticker}/"
        soup = get_page(url)

        if not soup:
            return ScraperResult(
                success=False,
                error=f"Failed to scrape data for ticker '{ticker}'",
                source="screener",
            )

        stock_dto = map_company_page(soup, ticker, url)

        return ScraperResult(
            success=True,
            data=stock_dto,
            source="screener",
        )

    def get_multiple(self, tickers: list[str]) -> ScraperResult[list[StockDTO]]:
        """Scrape technical data for multiple stocks.

        Args:
            tickers: List of stock ticker symbols.

        Returns:
            ScraperResult containing a list of StockDTO on success.
            Individual stock failures are handled gracefully.
        """
        stocks: list[StockDTO] = []
        failed: list[str] = []

        for i, ticker in enumerate(tickers):
            result = self.get_technical_data(ticker)
            if result.success and result.data:
                stocks.append(result.data)
            else:
                failed.append(ticker)
                logger.warning("Failed to scrape %s: %s", ticker, result.error)

            if i < len(tickers) - 1:
                time.sleep(REQUEST_DELAY)

        if not stocks:
            return ScraperResult(
                success=False,
                error=f"Failed to scrape any stocks. Failed tickers: {failed}",
                source="screener",
            )

        if failed:
            logger.warning("Some stocks failed to scrape: %s", failed)

        return ScraperResult(
            success=True,
            data=stocks,
            source="screener",
        )

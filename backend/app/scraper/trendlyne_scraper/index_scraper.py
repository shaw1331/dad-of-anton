from __future__ import annotations

import logging
import re
import time

from app.scraper.interfaces import IndexScraper
from app.scraper.models import ScraperResult, StockSummaryDTO
from app.scraper.trendlyne_scraper.config import BASE_URL, REQUEST_DELAY, SEARCH_API
from app.scraper.trendlyne_scraper.http import get_json, get_page
from app.scraper.trendlyne_scraper.mappers import map_index_search_result

logger = logging.getLogger(__name__)


class TrendlyneIndexScraper(IndexScraper):
    """IndexScraper implementation for trendlyne.com.

    Resolves an index ticker via the search API, then scrapes the
    constituent stocks table from the index overview page.
    """

    def _resolve_index(self, index_name: str) -> dict | None:
        """Search Trendlyne for an index and return its metadata."""
        url = f"{BASE_URL}{SEARCH_API}"
        params = {"term": index_name, "all-results": "true"}
        data = get_json(url, params=params)
        if not data:
            return None
        return map_index_search_result(data)

    def _extract_stocks(self, soup: object) -> list[dict[str, str]]:
        """Extract stock tickers and names from the index constituents table."""
        from bs4 import BeautifulSoup

        if not isinstance(soup, BeautifulSoup):
            return []

        stocks: list[dict[str, str]] = []

        # Find the stock table with class containing "stockdd"
        table = soup.find("table", class_=re.compile(r"stockdd"))
        if not table:
            return []

        for row in table.find_all("tr"):
            link = row.find("a", href=re.compile(r"/equity/\d+/"))
            if not link:
                continue

            href = link.get("href", "")
            name = link.get_text(strip=True)

            # Extract ticker from URL pattern: /equity/{id}/{TICKER}/{slug}/
            ticker_match = re.search(r"/equity/\d+/([A-Z0-9&]+)/", href)
            if ticker_match:
                ticker = ticker_match.group(1)
                stocks.append({
                    "ticker": ticker,
                    "name": name,
                    "url": href if href.startswith("http") else f"{BASE_URL}{href}",
                })

        return stocks

    def get_stocks(self, index_name: str) -> ScraperResult[list[StockSummaryDTO]]:
        """Scrape all stocks from a Trendlyne index page.

        Args:
            index_name: Index ticker (e.g., "NIFTY50", "SMALLCAP50").

        Returns:
            ScraperResult containing a list of StockSummaryDTO on success.
        """
        index_info = self._resolve_index(index_name)
        if not index_info:
            return ScraperResult(
                success=False,
                error=f"No Trendlyne index found for '{index_name}'",
                source="trendlyne",
            )

        stock_id = index_info["stock_id"]
        slug = index_info["slug"]
        url = f"{BASE_URL}/equity/{stock_id}/{index_info['ticker']}/{slug}/"

        logger.info("Fetching index page for %s at %s", index_name, url)
        soup = get_page(url)
        if not soup:
            return ScraperResult(
                success=False,
                error=f"Failed to fetch index page for '{index_name}'",
                source="trendlyne",
            )

        raw_stocks = self._extract_stocks(soup)
        logger.info("Found %d stocks in index %s", len(raw_stocks), index_name)

        stocks = [
            StockSummaryDTO(
                ticker=s["ticker"],
                name=s["name"],
                url=s["url"],
            )
            for s in raw_stocks
        ]

        return ScraperResult(
            success=True,
            data=stocks,
            source="trendlyne",
        )

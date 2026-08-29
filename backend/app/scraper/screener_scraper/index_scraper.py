from __future__ import annotations

import logging
import re
import time

from bs4 import BeautifulSoup

from app.scraper.interfaces import IndexScraper
from app.scraper.models import ScraperResult, StockSummaryDTO
from app.scraper.screener_scraper.config import BASE_URL, REQUEST_DELAY
from app.scraper.screener_scraper.http import get_page

logger = logging.getLogger(__name__)


def _get_total_pages(soup: BeautifulSoup) -> int:
    """Extract total pages from pagination info."""
    page_info = soup.select_one("[data-page-info]")
    if not page_info:
        return 1

    text = page_info.get_text()
    match = re.search(r"of\s+(\d+)", text)
    if match:
        return int(match.group(1))

    pagination_links = soup.select(".pagination a[href*='page=']")
    if pagination_links:
        pages: set[int] = set()
        for link in pagination_links:
            href = link.get("href", "")
            page_match = re.search(r"page=(\d+)", href)
            if page_match:
                pages.add(int(page_match.group(1)))
        return max(pages) if pages else 1

    return 1


def _extract_companies(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Extract company tickers and names from the constituents table."""
    companies: list[dict[str, str]] = []
    rows = soup.select("tr[data-row-company-id]")

    for row in rows:
        link = row.select_one("td.text a[href*='/company/']")
        if not link:
            continue

        href = link.get("href", "")
        name = link.get_text(strip=True)

        ticker_match = re.search(r"/company/([^/]+)/", href)
        if ticker_match:
            ticker = ticker_match.group(1)
            companies.append({
                "ticker": ticker,
                "name": name,
                "url": f"{BASE_URL}{href}",
            })

    return companies


class ScreenerIndexScraper(IndexScraper):
    """IndexScraper implementation for screener.in."""

    def get_stocks(self, index_name: str) -> ScraperResult[list[StockSummaryDTO]]:
        """Scrape all stocks from a screener.in index page.

        Args:
            index_name: Name of the index (e.g., "NIFTY50", "SMALLCAP50").

        Returns:
            ScraperResult containing a list of StockSummaryDTO on success.
        """
        slug = index_name.upper()

        all_companies: list[dict[str, str]] = []
        page = 1
        total_pages: int | None = None

        while True:
            if page == 1:
                url = f"{BASE_URL}/company/{slug}/"
            else:
                url = f"{BASE_URL}/company/{slug}/?page={page}"

            logger.info("Fetching page %d for index %s...", page, index_name)
            soup = get_page(url)

            if not soup:
                logger.error("Failed to fetch page %d", page)
                break

            if total_pages is None:
                total_pages = _get_total_pages(soup)
                logger.info("Total pages: %d", total_pages)

            companies = _extract_companies(soup)
            all_companies.extend(companies)
            logger.info("Found %d companies on page %d", len(companies), page)

            if page >= total_pages:
                break

            page += 1
            time.sleep(REQUEST_DELAY)

        stocks = [
            StockSummaryDTO(
                ticker=c["ticker"],
                name=c["name"],
                url=c["url"],
            )
            for c in all_companies
        ]

        return ScraperResult(
            success=True,
            data=stocks,
            source="screener",
        )

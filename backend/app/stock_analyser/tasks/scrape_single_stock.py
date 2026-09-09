from __future__ import annotations

import logging
from typing import Any

from app.scraper.factory import ScraperFactory

logger = logging.getLogger(__name__)


class ScrapeSingleStockTask:
    """Scrapes screener data for a single stock ticker.

    Uses the existing ScreenerStockScraper to fetch fundamentals.
    Produces the same output format as ScrapeStocksTask so downstream
    tasks (ScrapeTrendlyneTask, ScrapeNewsTask, AnalyzeStocksTask) work unchanged.
    """

    name = "scrape_stocks"

    def run(self, ctx: Any) -> None:
        ticker = ctx.get_input("ticker")

        stock_scraper = ScraperFactory.get_stock_scraper("screener")
        result = stock_scraper.get_technical_data(ticker)

        if not result.success:
            raise Exception(result.error)

        stock = result.data
        logger.info("Scraped screener data for %s — %s", ticker, stock.name)

        ctx.set_output(self.name, {
            "index": "single_stock",
            "stocks": [stock.model_dump(mode="json")],
        })

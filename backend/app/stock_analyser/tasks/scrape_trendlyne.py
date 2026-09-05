from __future__ import annotations

import logging
from typing import Any

from app.scraper.trendlyne_scraper.stock_scraper import TrendlyneStockScraper

logger = logging.getLogger(__name__)


class ScrapeTrendlyneTask:
    """Scrapes additional data for each stock from Trendlyne.

    Reads the stocks already scraped by ScrapeStocksTask and enriches them
    with Trendlyne technical data.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "scrape_trendlyne"

    def run(self, ctx: Any) -> None:
        stocks_output = ctx.get_output("scrape_stocks")
        if not stocks_output:
            raise Exception("No scraped stocks found. Run ScrapeStocksTask first.")

        stocks = stocks_output["stocks"]
        tickers = [s["ticker"] for s in stocks]
        logger.info("Scraping Trendlyne data for %d stocks", len(tickers))

        scraper = TrendlyneStockScraper()
        trendlyne_result = scraper.get_multiple(tickers)

        if not trendlyne_result.success:
            raise Exception(trendlyne_result.error)

        trendlyne_stocks = [s.model_dump(mode="json") for s in trendlyne_result.data]

        # Store raw Trendlyne output separately
        ctx.set_output(self.name, {
            "index": stocks_output["index"],
            "stocks": trendlyne_stocks,
        })

        logger.info("Trendlyne enrichment complete for %d stocks", len(trendlyne_stocks))

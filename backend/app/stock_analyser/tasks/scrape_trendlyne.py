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

        trendlyne_map: dict[str, dict] = {}
        for stock_dto in trendlyne_result.data:
            trendlyne_map[stock_dto.ticker] = stock_dto.model_dump(mode="json")

        enriched: list[dict] = []
        for stock in stocks:
            ticker = stock["ticker"]
            trendlyne_data = trendlyne_map.get(ticker)
            if trendlyne_data:
                merged = {**stock, "trendlyne": trendlyne_data}
            else:
                merged = {**stock, "trendlyne": None}
                logger.warning("No Trendlyne data for %s", ticker)
            enriched.append(merged)

        ctx.set_output("scrape_stocks", {
            "index": stocks_output["index"],
            "stocks": enriched,
        })

        logger.info("Trendlyne enrichment complete for %d stocks", len(enriched))

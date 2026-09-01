from __future__ import annotations

import logging
from typing import Any

from app.scraper.factory import ScraperFactory

logger = logging.getLogger(__name__)


class ScrapeTickersTask:
    """Scrapes stock data for a list of tickers.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "scrape_tickers"

    def __init__(self, source: str = "screener") -> None:
        self.source = source

    def run(self, ctx: Any) -> None:
        tickers_raw = ctx.get_input("tickers")
        if not tickers_raw:
            raise ValueError("No tickers provided")

        tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
        if not tickers:
            raise ValueError("No valid tickers after parsing")

        logger.info("Scraping data for %d tickers: %s", len(tickers), ", ".join(tickers))

        stock_scraper = ScraperFactory.get_stock_scraper(self.source)
        result = stock_scraper.get_multiple(tickers)

        if not result.success:
            raise Exception(result.error)

        stocks = result.data
        for i, stock in enumerate(stocks, 1):
            logger.info("  [%d/%d] %s — %s", i, len(stocks), stock.ticker, getattr(stock, "name", stock.ticker))

        ctx.set_output(self.name, {
            "tickers": tickers,
            "stocks": [s.model_dump(mode="json") for s in stocks],
        })

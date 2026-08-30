from __future__ import annotations

import logging
from typing import Any

from app.scraper.factory import ScraperFactory

logger = logging.getLogger(__name__)


class ScrapeStocksTask:
    """Scrapes stock data for a given index.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "scrape_stocks"

    def __init__(self, source: str = "screener") -> None:
        self.source = source

    def run(self, ctx: Any) -> None:
        index = ctx.get_input("index")

        index_scraper = ScraperFactory.get_index_scraper(self.source)
        stocks_result = index_scraper.get_stocks(index)

        if not stocks_result.success:
            raise Exception(stocks_result.error)

        stock_scraper = ScraperFactory.get_stock_scraper(self.source)
        tickers = [s.ticker for s in stocks_result.data]
        technical_result = stock_scraper.get_multiple(tickers)

        if not technical_result.success:
            raise Exception(technical_result.error)

        stocks = technical_result.data
        tickers = [s.ticker for s in stocks]
        names = [getattr(s, "name", s.ticker) for s in stocks]

        logger.info("Scraped %d stocks for index '%s': %s", len(stocks), index, ", ".join(tickers))
        for i, (ticker, name) in enumerate(zip(tickers, names), 1):
            logger.info("  [%d/%d] %s — %s", i, len(stocks), ticker, name)

        ctx.set_output(self.name, {
            "index": index,
            "stocks": [s.model_dump(mode="json") for s in stocks],
        })

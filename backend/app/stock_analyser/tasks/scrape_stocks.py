from __future__ import annotations

import logging
import random
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
        num_stocks = ctx.get_input("num_stocks")
        selection_criteria = ctx.get_input("selection_criteria") or "all"

        index_scraper = ScraperFactory.get_index_scraper(self.source)
        stocks_result = index_scraper.get_stocks(index)

        if not stocks_result.success:
            raise Exception(stocks_result.error)

        all_stocks = stocks_result.data
        logger.info("Found %d stocks in index '%s'", len(all_stocks), index)

        if num_stocks and num_stocks > 0:
            if selection_criteria == "top":
                selected = all_stocks[:num_stocks]
                logger.info("Selected top %d stocks", num_stocks)
            elif selection_criteria == "bottom":
                selected = all_stocks[-num_stocks:]
                logger.info("Selected bottom %d stocks", num_stocks)
            elif selection_criteria == "random":
                count = min(num_stocks, len(all_stocks))
                selected = random.sample(all_stocks, count)
                logger.info("Selected %d random stocks", count)
            else:
                selected = all_stocks
        else:
            selected = all_stocks
            logger.info("Using all %d stocks (no limit set)", len(all_stocks))

        tickers = [s.ticker for s in selected]
        logger.info("Scraping technical data for: %s", ", ".join(tickers))

        stock_scraper = ScraperFactory.get_stock_scraper(self.source)
        technical_result = stock_scraper.get_multiple(tickers)

        if not technical_result.success:
            raise Exception(technical_result.error)

        stocks = technical_result.data
        for i, stock in enumerate(stocks, 1):
            logger.info("  [%d/%d] %s — %s", i, len(stocks), stock.ticker, getattr(stock, "name", stock.ticker))

        ctx.set_output(self.name, {
            "index": index,
            "stocks": [s.model_dump(mode="json") for s in stocks],
        })

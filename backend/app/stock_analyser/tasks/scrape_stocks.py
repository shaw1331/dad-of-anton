from __future__ import annotations

from typing import Any

from app.scraper.factory import ScraperFactory


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

        ctx.set_output(self.name, {
            "index": index,
            "stocks": [s.model_dump(mode="json") for s in technical_result.data],
        })

from __future__ import annotations

from typing import Any

from app.scraper.tradingview_scraper import get_candles


class ScrapeTradingViewTask:
    name = "scrape_tradingview"

    def run(self, ctx: Any) -> None:
        stocks_output = ctx.get_output("scrape_stocks")
        if not stocks_output:
            raise Exception("No scraped stocks found. Run ScrapeStocksTask first.")
        exchange = str(ctx.get_input("exchange") or "NSE").upper()
        candles: dict[str, list[dict]] = {}
        for stock in stocks_output["stocks"]:
            ticker = stock["ticker"]
            result = get_candles(ticker, exchange=exchange, interval="1D", bars=60)
            candles[ticker] = [] if result is None else [c.model_dump(mode="json") for c in result.candles]
        ctx.set_output(self.name, {"candles": candles, "bars": 60, "exchange": exchange})

from __future__ import annotations

import logging
from typing import Any

from app.stock_analyser.analysis.levels import compute_levels

logger = logging.getLogger(__name__)


class CalculateLevelsTask:
    name = "calculate_levels"

    def run(self, ctx: Any) -> None:
        scrape_output = ctx.get_output("scrape_stocks")
        if not scrape_output:
            raise Exception("No scraped stocks found. Run ScrapeStocksTask first.")

        stocks = scrape_output["stocks"]
        trendlyne_output = ctx.get_output("scrape_trendlyne")
        trendlyne_map: dict[str, dict] = {}
        if trendlyne_output:
            trendlyne_map = {s["ticker"]: s for s in trendlyne_output.get("stocks", [])}

        tradingview_map = (ctx.get_output("scrape_tradingview") or {}).get("candles", {})

        levels: dict[str, dict] = {}
        for stock in stocks:
            ticker = stock["ticker"]
            tl_data = (trendlyne_map.get(ticker) or {}).get("data", {})
            candles = tradingview_map.get(ticker, [])
            try:
                result = compute_levels(tl_data, candles)
                levels[ticker] = result.model_dump()
                logger.info("Levels for %s: %s — %s", ticker, result.recommendation, result.level_reasoning)
            except Exception as e:
                logger.error("Levels calculation failed for %s: %s", ticker, str(e))
                levels[ticker] = {"error": str(e)}

        ctx.set_output(self.name, {"levels": levels})
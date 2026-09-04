from __future__ import annotations

import logging
from typing import Any

from app.scraper.groww_scraper import GrowwNewsScraper

logger = logging.getLogger(__name__)


class ScrapeNewsTask:
    """Scrapes news articles for all stocks using GrowwNewsScraper.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "scrape_news"

    def run(self, ctx: Any) -> None:
        enable_news = ctx.get_input("enable_news")
        if not enable_news:
            ctx.set_output(self.name, {"news": {}, "total_articles": 0})
            return

        stocks_output = ctx.get_output("scrape_stocks")
        if not stocks_output:
            raise Exception("No scraped stocks found. Run ScrapeStocksTask first.")

        stocks = stocks_output["stocks"]
        lookback_days = ctx.get_input("news_lookback_days") or 15

        logger.info("Scraping news for %d stocks (lookback: %d days)",
                     len(stocks), lookback_days)

        scraper = GrowwNewsScraper()
        all_news: dict[str, list[dict]] = {}
        total = 0

        for i, stock in enumerate(stocks, 1):
            ticker = stock.get("ticker", "UNKNOWN")
            logger.info("[%d/%d] Fetching news for %s...", i, len(stocks), ticker)

            result = scraper.get_news(ticker, lookback_days)
            if result.success and result.data:
                articles = [a.model_dump(mode="json") for a in result.data]
                all_news[ticker] = articles
                total += len(articles)
                logger.info("[%d/%d] %s — found %d articles",
                            i, len(stocks), ticker, len(articles))
            else:
                logger.warning("[%d/%d] %s — no news: %s",
                               i, len(stocks), ticker, result.error)
                all_news[ticker] = []

        logger.info("News scraping complete: %d articles across %d stocks",
                     total, len(stocks))

        ctx.set_output(self.name, {
            "news": all_news,
            "total_articles": total,
        })

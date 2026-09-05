"""Integration tests for ScrapeNewsTask.

Uses real GrowwNewsScraper against live Groww API.
No mocking — tests the full scraping pipeline end-to-end.
"""
from __future__ import annotations

import pytest

from app.scraper.groww_scraper import GrowwNewsScraper
from app.stock_analyser.tasks.scrape_news import ScrapeNewsTask
from tests.utils.context import make_context


@pytest.fixture
def task():
    return ScrapeNewsTask()


class TestScrapeNewsTask:
    def test_scrape_news_success(self, task, scrape_stocks_output):
        ctx = make_context(
            input={"enable_news": True, "news_lookback_days": 7},
            outputs={"scrape_stocks": scrape_stocks_output},
        )
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert "news" in output
        assert "total_articles" in output
        assert isinstance(output["news"], dict)
        assert isinstance(output["total_articles"], int)

        for ticker, articles in output["news"].items():
            assert isinstance(articles, list)
            for article in articles:
                assert "url" in article
                assert "source" in article

    def test_scrape_news_disabled(self, task):
        ctx = make_context(input={"enable_news": False})
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert output == {"news": {}, "total_articles": 0}

    def test_scrape_news_unknown_ticker(self, task):
        bad_stocks = {
            "index": "TEST",
            "stocks": [{"ticker": "ZZZZZZ99", "name": "Fake Corp"}],
        }
        ctx = make_context(
            input={"enable_news": True, "news_lookback_days": 7},
            outputs={"scrape_stocks": bad_stocks},
        )
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert output["news"]["ZZZZZZ99"] == []
        assert output["total_articles"] == 0

    def test_scrape_news_no_stocks(self, task):
        ctx = make_context(input={"enable_news": True})
        with pytest.raises(Exception, match="Run ScrapeStocksTask first"):
            task.run(ctx)

    def test_scrape_news_single_stock(self, task):
        stocks = {
            "index": "TEST",
            "stocks": [{"ticker": "TCS", "name": "Tata Consultancy Services"}],
        }
        ctx = make_context(
            input={"enable_news": True, "news_lookback_days": 30},
            outputs={"scrape_stocks": stocks},
        )
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert "TCS" in output["news"]
        assert isinstance(output["news"]["TCS"], list)

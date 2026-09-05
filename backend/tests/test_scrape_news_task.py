"""Tests for ScrapeNewsTask."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.scraper.groww_scraper.models import NewsArticle
from app.scraper.models import ScraperResult
from app.stock_analyser.tasks.scrape_news import ScrapeNewsTask
from tests.utils.builders import build_news_article, build_scraper_result
from tests.utils.context import make_context


@pytest.fixture
def task():
    return ScrapeNewsTask()


class TestScrapeNewsTask:
    @patch("app.stock_analyser.tasks.scrape_news.GrowwNewsScraper")
    def test_scrape_news_success(self, MockScraper, task, scrape_stocks_output):
        article = NewsArticle(
            id="1", summary="Test", url="https://example.com",
            pub_date="2026-09-04T12:00:00Z", source="Test",
        )
        mock_instance = MockScraper.return_value
        mock_instance.get_news.return_value = ScraperResult(
            success=True, data=[article], source="groww",
        )

        ctx = make_context(
            input={"enable_news": True, "news_lookback_days": 7},
            outputs={"scrape_stocks": scrape_stocks_output},
        )
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert output["total_articles"] == 2
        assert "RELIANCE" in output["news"]
        assert "TCS" in output["news"]
        assert len(output["news"]["RELIANCE"]) == 1

    def test_scrape_news_disabled(self, task):
        ctx = make_context(input={"enable_news": False})
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert output == {"news": {}, "total_articles": 0}

    @patch("app.stock_analyser.tasks.scrape_news.GrowwNewsScraper")
    def test_scrape_news_partial_failure(self, MockScraper, task, scrape_stocks_output):
        article = NewsArticle(
            id="1", summary="Test", url="https://example.com",
            pub_date="2026-09-04T12:00:00Z", source="Test",
        )
        mock_instance = MockScraper.return_value

        def side_effect(ticker, lookback):
            if ticker == "RELIANCE":
                return ScraperResult(success=True, data=[article], source="groww")
            return ScraperResult(success=False, error="Not found", source="groww")

        mock_instance.get_news.side_effect = side_effect

        ctx = make_context(
            input={"enable_news": True, "news_lookback_days": 7},
            outputs={"scrape_stocks": scrape_stocks_output},
        )
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert len(output["news"]["RELIANCE"]) == 1
        assert output["news"]["TCS"] == []
        assert output["total_articles"] == 1

    def test_scrape_news_no_stocks(self, task):
        ctx = make_context(input={"enable_news": True})
        with pytest.raises(Exception, match="Run ScrapeStocksTask first"):
            task.run(ctx)

    @patch("app.stock_analyser.tasks.scrape_news.GrowwNewsScraper")
    def test_scrape_news_api_exception(self, MockScraper, task, scrape_stocks_output):
        mock_instance = MockScraper.return_value
        mock_instance.get_news.side_effect = ConnectionError("Network error")

        ctx = make_context(
            input={"enable_news": True, "news_lookback_days": 7},
            outputs={"scrape_stocks": scrape_stocks_output},
        )
        task.run(ctx)

        output = ctx.get_output("scrape_news")
        assert output["news"]["RELIANCE"] == []
        assert output["news"]["TCS"] == []
        assert output["total_articles"] == 0

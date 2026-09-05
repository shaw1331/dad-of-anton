"""Integration tests for AnalyzeNewsTask.

Uses real AgentFactory + real LLM (Ollama) end-to-end.
No mocking — tests the full analysis pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.stock_analyser.tasks.analyze_news import AnalyzeNewsTask
from tests.utils.context import make_context

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def task():
    return AnalyzeNewsTask()


@pytest.fixture
def real_news():
    with open(_FIXTURES_DIR / "sample_news.json") as f:
        return json.load(f)


class TestAnalyzeNewsTask:
    def test_analyze_news_success(self, task, real_news):
        ctx = make_context(
            input={"enable_news": True},
            outputs={"scrape_news": real_news},
        )
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert output["total_analyzed"] >= 1
        assert "RELIANCE" in output["analyses"]
        assert len(output["analyses"]["RELIANCE"]) >= 1

        article = output["analyses"]["RELIANCE"][0]
        assert "impact" in article
        assert "trader_sentiment" in article
        assert "detailed_summary" in article

    def test_analyze_news_disabled(self, task):
        ctx = make_context(input={"enable_news": False})
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert output == {"analyses": {}, "total_analyzed": 0}

    def test_analyze_news_no_news(self, task):
        ctx = make_context(input={"enable_news": True})
        with pytest.raises(Exception, match="Run ScrapeNewsTask first"):
            task.run(ctx)

    def test_analyze_news_empty_articles(self, task):
        news = {"news": {"RELIANCE": []}, "total_articles": 0}
        ctx = make_context(
            input={"enable_news": True},
            outputs={"scrape_news": news},
        )
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert output["analyses"]["RELIANCE"] == []
        assert output["total_analyzed"] == 0

    def test_analyze_news_multiple_tickers(self, task):
        news = {
            "news": {
                "RELIANCE": [
                    {"url": "https://example.com/r1", "source": "Test", "summary": "Reliance Q2 results."}
                ],
                "TCS": [
                    {"url": "https://example.com/t1", "source": "Test", "summary": "TCS wins new deal."}
                ],
            },
            "total_articles": 2,
        }
        ctx = make_context(
            input={"enable_news": True},
            outputs={"scrape_news": news},
        )
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert "RELIANCE" in output["analyses"]
        assert "TCS" in output["analyses"]
        assert output["total_analyzed"] >= 2

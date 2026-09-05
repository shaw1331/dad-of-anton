"""Tests for AnalyzeNewsTask."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ai.models import AgentResult
from app.stock_analyser.tasks.analyze_news import AnalyzeNewsTask
from tests.utils.builders import build_agent_result, build_analyzed_article
from tests.utils.context import make_context


@pytest.fixture
def task():
    return AnalyzeNewsTask()


@pytest.fixture
def news_with_articles():
    return {
        "news": {
            "RELIANCE": [
                {"url": "https://example.com/article1", "source": "Test", "summary": "Test summary"}
            ]
        },
        "total_articles": 1,
    }


class TestAnalyzeNewsTask:
    @patch("app.stock_analyser.tasks.analyze_news.AgentFactory")
    def test_analyze_news_success(self, MockFactory, task, news_with_articles):
        mock_agent = MagicMock()
        mock_agent.run.return_value = build_agent_result(
            data={
                "articles": [build_analyzed_article()],
                "ticker": "RELIANCE",
                "total_articles": 1,
            },
        )
        MockFactory.get.return_value = mock_agent

        ctx = make_context(
            input={"enable_news": True},
            outputs={"scrape_news": news_with_articles},
        )
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert output["total_analyzed"] == 1
        assert "RELIANCE" in output["analyses"]

    def test_analyze_news_disabled(self, task):
        ctx = make_context(input={"enable_news": False})
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert output == {"analyses": {}, "total_analyzed": 0}

    @patch("app.stock_analyser.tasks.analyze_news.AgentFactory")
    def test_analyze_news_partial_failure(self, MockFactory, task):
        mock_agent = MagicMock()

        def side_effect(input_data):
            ticker = input_data["ticker"]
            if ticker == "RELIANCE":
                return build_agent_result(
                    data={"articles": [build_analyzed_article()], "ticker": "RELIANCE", "total_articles": 1},
                )
            return build_agent_result(success=False, error="LLM failed")

        mock_agent.run.side_effect = side_effect
        MockFactory.get.return_value = mock_agent

        news = {
            "news": {
                "RELIANCE": [{"url": "https://example.com/a1", "source": "Test", "summary": "S1"}],
                "TCS": [{"url": "https://example.com/a2", "source": "Test", "summary": "S2"}],
            },
            "total_articles": 2,
        }
        ctx = make_context(
            input={"enable_news": True},
            outputs={"scrape_news": news},
        )
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert len(output["analyses"]["RELIANCE"]) == 1
        assert output["analyses"]["TCS"] == []

    def test_analyze_news_no_news(self, task):
        ctx = make_context(input={"enable_news": True})
        with pytest.raises(Exception, match="Run ScrapeNewsTask first"):
            task.run(ctx)

    @patch("app.stock_analyser.tasks.analyze_news.AgentFactory")
    def test_analyze_news_agent_crash(self, MockFactory, task, news_with_articles):
        mock_agent = MagicMock()
        mock_agent.run.side_effect = RuntimeError("LLM crashed")
        MockFactory.get.return_value = mock_agent

        ctx = make_context(
            input={"enable_news": True},
            outputs={"scrape_news": news_with_articles},
        )
        task.run(ctx)

        output = ctx.get_output("analyze_news")
        assert output["analyses"]["RELIANCE"] == []

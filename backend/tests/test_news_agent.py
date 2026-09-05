"""Integration tests for NewsAnalysisAgent.

Uses real LLM, real trafilatura, real pypdf — full end-to-end.
No mocking.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.ai.factory import AgentFactory
from app.ai.models import AnalyzedNewsArticle, NewsAnalysisResult

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "app" / "stock_analyser" / "analysis" / "prompts"


@pytest.fixture
def agent():
    return AgentFactory.get("news_analysis", output_model=NewsAnalysisResult)


@pytest.fixture
def system_prompt():
    return (_PROMPT_DIR / "news_analysis.md").read_text()


class TestNewsAnalysisAgent:
    def test_pdf_url_detection(self, agent):
        assert agent._is_pdf_url("https://bseindia.com/file.pdf") is True
        assert agent._is_pdf_url("https://example.com/article.html") is False
        assert agent._is_pdf_url("https://example.com/news") is False

    def test_fetch_html_content(self, agent):
        content = agent._fetch_content("https://www.moneycontrol.com/news/business/")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_fetch_empty_url(self, agent):
        result = agent._fetch_content("")
        assert result == ""

    def test_analyze_single_article(self, agent, system_prompt):
        article = {
            "url": "https://www.moneycontrol.com/news/business/reliance-industries",
            "source": "Moneycontrol",
            "summary": "Reliance Industries Q2 profit up 12% on strong retail growth.",
            "pub_date": "2026-09-04T10:30:00Z",
        }
        result = agent._analyze_single(article, "RELIANCE", system_prompt)

        assert isinstance(result, dict)
        assert result["ticker"] == "RELIANCE"
        assert "impact" in result
        assert "trader_sentiment" in result
        assert "detailed_summary" in result

    def test_run_single_article(self, agent, system_prompt):
        articles = [
            {
                "url": "https://www.moneycontrol.com/news/business/reliance-industries",
                "source": "Moneycontrol",
                "summary": "Reliance Industries reports strong Q2 results.",
                "pub_date": "2026-09-04T10:30:00Z",
            }
        ]
        result = agent.run({
            "ticker": "RELIANCE",
            "articles": articles,
            "system_prompt": system_prompt,
        })

        assert result.success is True
        assert len(result.data["articles"]) == 1
        assert result.data["ticker"] == "RELIANCE"

    def test_run_multiple_articles(self, agent, system_prompt):
        articles = [
            {
                "url": "https://www.moneycontrol.com/news/business/reliance-industries",
                "source": "Moneycontrol",
                "summary": "Reliance Q2 profit up 12%.",
                "pub_date": "2026-09-04T10:30:00Z",
            },
            {
                "url": "https://economictimes.indiatimes.com/markets/stocks/news/reliance",
                "source": "Economic Times",
                "summary": "Reliance retail segment drives growth.",
                "pub_date": "2026-09-03T15:00:00Z",
            },
        ]
        result = agent.run({
            "ticker": "RELIANCE",
            "articles": articles,
            "system_prompt": system_prompt,
        })

        assert result.success is True
        assert len(result.data["articles"]) == 2
        article = result.data["articles"][0]
        assert article["impact"] in ["high", "medium", "low", "none"]
        assert article["trader_sentiment"] in [
            "bullish", "bearish", "neutral",
            "very_bullish", "very_bearish",
        ]

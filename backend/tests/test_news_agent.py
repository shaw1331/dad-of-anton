"""Integration test for NewsAnalysisAgent.

Edit tests/fixtures/sample_articles.json to change inputs.
Run: cd backend && python -m pytest tests/test_news_agent.py -v -s
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.factory import AgentFactory
from app.ai.models import NewsAnalysisResult

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "app" / "stock_analyser" / "analysis" / "prompts"
_FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_test_cases():
    with open(_FIXTURES_DIR / "sample_articles.json") as f:
        return json.load(f)


@pytest.fixture
def agent():
    return AgentFactory.get("news_analysis", output_model=NewsAnalysisResult)


@pytest.fixture
def system_prompt():
    return (_PROMPT_DIR / "news_analysis.md").read_text()


TEST_CASES = load_test_cases()


@pytest.mark.parametrize(
    "case",
    TEST_CASES,
    ids=[c["ticker"] for c in TEST_CASES],
)
def test_analyze_article(agent, system_prompt, case):
    ticker = case["ticker"]
    articles = case["articles"]

    result = agent.run({
        "ticker": ticker,
        "articles": articles,
        "system_prompt": system_prompt,
    })

    assert result.success is True, f"Agent failed for {ticker}: {result.error}"

    print(f"\n{'='*60}")
    print(f"TICKER: {ticker}")
    print(f"Articles analyzed: {len(result.data['articles'])}")
    print(f"{'='*60}")

    for i, article in enumerate(result.data["articles"], 1):
        print(f"\n--- Article {i} ---")
        print(f"URL:    {article.get('url', 'N/A')}")
        print(f"Source: {article.get('source', 'N/A')}")
        print(f"Impact: {article.get('impact', 'N/A')}")
        print(f"Sentiment: {article.get('trader_sentiment', 'N/A')}")
        print(f"Summary: {article.get('detailed_summary', 'N/A')}")
        print(f"Reasoning: {article.get('impact_reasoning', 'N/A')}")

    print(f"\n{'='*60}\n")

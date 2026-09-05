"""Integration test for AnalyzeNewsTask.

Edit tests/fixtures/sample_news.json to change inputs.
Run: cd backend && python -m pytest tests/test_analyze_news_task.py -v -s
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
def news_data():
    with open(_FIXTURES_DIR / "sample_news.json") as f:
        return json.load(f)


def test_analyze_news(task, news_data):
    ctx = make_context(
        input={"enable_news": True},
        outputs={"scrape_news": news_data},
    )
    task.run(ctx)

    output = ctx.get_output("analyze_news")
    assert output["total_analyzed"] >= 1

    print(f"\n{'='*60}")
    print(f"Total analyzed: {output['total_analyzed']}")
    print(f"{'='*60}")

    for ticker, articles in output["analyses"].items():
        print(f"\nTICKER: {ticker}")
        for i, article in enumerate(articles, 1):
            print(f"  --- Article {i} ---")
            print(f"  Impact:    {article.get('impact', 'N/A')}")
            print(f"  Sentiment: {article.get('trader_sentiment', 'N/A')}")
            print(f"  Summary:   {article.get('detailed_summary', 'N/A')}")
            print(f"  Reasoning: {article.get('impact_reasoning', 'N/A')}")

    print(f"\n{'='*60}\n")


def test_analyze_news_disabled(task):
    ctx = make_context(input={"enable_news": False})
    task.run(ctx)

    output = ctx.get_output("analyze_news")
    assert output == {"analyses": {}, "total_analyzed": 0}


def test_analyze_news_no_news(task):
    ctx = make_context(input={"enable_news": True})
    with pytest.raises(Exception, match="Run ScrapeNewsTask first"):
        task.run(ctx)

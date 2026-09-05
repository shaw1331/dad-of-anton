"""Shared pytest fixtures for integration tests."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.utils.builders import (
    build_agent_result,
    build_analyzed_article,
    build_news_article,
    build_scraper_result,
    build_stock,
)
from tests.utils.context import make_context

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def workflow_inputs() -> dict:
    return {
        "index": "NIFTY50",
        "enable_news": True,
        "news_lookback_days": 7,
    }


@pytest.fixture
def workflow_ctx(workflow_inputs):
    return make_context(input=workflow_inputs)


@pytest.fixture
def workflow_ctx_disabled():
    return make_context(input={"enable_news": False})


@pytest.fixture
def sample_stocks() -> list[dict]:
    with open(_FIXTURES_DIR / "sample_stocks.json") as f:
        return json.load(f)


@pytest.fixture
def sample_news_html() -> dict:
    with open(_FIXTURES_DIR / "sample_news_html.json") as f:
        return json.load(f)


@pytest.fixture
def sample_news_pdf() -> dict:
    with open(_FIXTURES_DIR / "sample_news_pdf.json") as f:
        return json.load(f)


@pytest.fixture
def scrape_stocks_output(sample_stocks) -> dict:
    return {"index": "NIFTY50", "stocks": sample_stocks}


@pytest.fixture
def scrape_news_output_html(sample_news_html) -> dict:
    return {
        "news": {"WOCKPHARMA": [sample_news_html]},
        "total_articles": 1,
    }


@pytest.fixture
def scrape_news_output_pdf(sample_news_pdf) -> dict:
    return {
        "news": {"PFC": [sample_news_pdf]},
        "total_articles": 1,
    }


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.run.return_value = build_agent_result(
        success=True,
        data={
            "articles": [build_analyzed_article()],
            "ticker": "RELIANCE",
            "total_articles": 1,
        },
    )
    return agent


@pytest.fixture
def mock_scraper():
    scraper = MagicMock()
    scraper.get_news.return_value = build_scraper_result(
        success=True,
        data=[build_news_article()],
    )
    return scraper

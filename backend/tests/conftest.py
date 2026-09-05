"""Shared pytest fixtures for integration tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.utils.context import make_context

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


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

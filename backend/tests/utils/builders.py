"""Mock data builders for tests."""
from __future__ import annotations

from app.ai.models import AgentResult, AnalyzedNewsArticle, NewsImpact
from app.scraper.groww_scraper.models import NewsArticle
from app.scraper.models import ScraperResult


def build_stock(name="Test Corp", ticker="TEST", bse="500001", sector="Finance") -> dict:
    return {"name": name, "ticker": ticker, "bse_code": bse, "sector": sector}


def build_news_article(
    url="https://example.com/article",
    summary="Test summary",
    source="Test Source",
    pub_date="2026-09-04T12:00:00Z",
) -> dict:
    return {"url": url, "summary": summary, "source": source, "pub_date": pub_date}


def build_analyzed_article(
    ticker="RELIANCE",
    news_id="12345",
    url="https://example.com/article",
    source="Test Source",
    pub_date="2026-09-04T12:00:00Z",
    impact="medium",
    trader_sentiment="neutral",
) -> dict:
    return {
        "ticker": ticker,
        "news_id": news_id,
        "url": url,
        "source": source,
        "pub_date": pub_date,
        "raw_summary": "Test summary",
        "detailed_summary": "Detailed test summary",
        "impact": impact,
        "impact_reasoning": "Test impact reasoning",
        "trader_sentiment": trader_sentiment,
    }


def build_agent_result(
    success=True, data=None, error=None, graph_name="news_analysis"
) -> AgentResult:
    return AgentResult(
        success=success,
        data=data or {"articles": [], "ticker": "RELIANCE", "total_articles": 0},
        error=error,
        graph_name=graph_name,
    )


def build_scraper_result(success=True, data=None, error=None) -> ScraperResult:
    return ScraperResult(
        success=success,
        data=data or [],
        error=error,
        source="groww",
    )

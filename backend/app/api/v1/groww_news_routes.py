from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Query

from app.scraper.groww_scraper import GrowwNewsScraper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groww-news", tags=["groww-news"])

scraper = GrowwNewsScraper()


@router.get("")
def get_groww_news(
    ticker: str,
    days: int = Query(default=15, ge=1, le=90, description="Lookback days (1-90)"),
):
    """Fetch recent stock news from Groww for a given ticker."""
    if not ticker.strip():
        raise HTTPException(status_code=422, detail="Ticker is required")

    start = time.time()

    result = scraper.search_ticker(ticker)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No Groww stock found for ticker '{ticker}'"
        )

    groww_contract_id, company_name = result

    news_result = scraper.get_news(ticker, lookback_days=days)
    if not news_result.success:
        raise HTTPException(status_code=502, detail=news_result.error)

    took_ms = round((time.time() - start) * 1000)

    return {
        "ticker": ticker,
        "groww_contract_id": groww_contract_id,
        "company_name": company_name,
        "articles": [a.model_dump(mode="json") for a in news_result.data],
        "count": len(news_result.data),
        "took_ms": took_ms,
    }

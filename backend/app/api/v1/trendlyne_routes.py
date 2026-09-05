from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Query

from app.scraper.trendlyne_scraper.stock_scraper import TrendlyneStockScraper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trendlyne", tags=["trendlyne"])

scraper = TrendlyneStockScraper()


@router.get("")
def get_trendlyne_technicals(
    ticker: str,
):
    """Fetch technical indicator data from Trendlyne for a given ticker."""
    if not ticker.strip():
        raise HTTPException(status_code=422, detail="Ticker is required")

    start = time.time()

    result = scraper.get_technical_data(ticker)
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)

    took_ms = round((time.time() - start) * 1000)

    return {
        "ticker": ticker,
        "stock": result.data.model_dump(mode="json"),
        "took_ms": took_ms,
    }

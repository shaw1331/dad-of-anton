from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scraper.tradingview_scraper import get_candles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tradingview", tags=["tradingview"])


class CandlesRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    interval: str = "1D"
    bars: int = 30


@router.get("/candles")
def fetch_candles(symbol: str, exchange: str = "NSE", interval: str = "1D", bars: int = 30):
    result = get_candles(symbol=symbol, exchange=exchange, interval=interval, bars=bars)

    if result is None:
        msg = f"Symbol '{symbol}' not found on {exchange}. Check the ticker name."
        raise HTTPException(status_code=404, detail=msg)

    return result.model_dump(mode="json")


@router.post("/candles")
def post_candles(request: CandlesRequest):
    return fetch_candles(
        symbol=request.symbol,
        exchange=request.exchange,
        interval=request.interval,
        bars=request.bars,
    )

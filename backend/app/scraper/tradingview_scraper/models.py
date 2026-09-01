from __future__ import annotations

from pydantic import BaseModel, Field


class CandleDTO(BaseModel):
    datetime: str = ""
    open: float = 0
    high: float = 0
    low: float = 0
    close: float = 0
    volume: float = 0


class CandlesResult(BaseModel):
    symbol: str
    exchange: str
    interval: str
    candles: list[CandleDTO] = Field(default_factory=list)

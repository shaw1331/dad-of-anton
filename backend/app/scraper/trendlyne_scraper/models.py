from __future__ import annotations

from pydantic import BaseModel


class TrendlyneStockData(BaseModel):
    ticker: str
    name: str
    url: str

    # EMA
    ema_5: float | None = None
    ema_10: float | None = None
    ema_12: float | None = None
    ema_20: float | None = None
    ema_26: float | None = None
    ema_50: float | None = None
    ema_100: float | None = None
    ema_200: float | None = None

    # SMA
    sma_5: float | None = None
    sma_10: float | None = None
    sma_20: float | None = None
    sma_30: float | None = None
    sma_50: float | None = None
    sma_100: float | None = None
    sma_150: float | None = None
    sma_200: float | None = None

    # Momentum
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    adx: float | None = None
    atr: float | None = None
    mfi: float | None = None
    cci: float | None = None
    roc_21: float | None = None
    roc_125: float | None = None
    williams_r: float | None = None

    # Support/Resistance
    pivot: float | None = None
    r1: float | None = None
    r2: float | None = None
    r3: float | None = None
    s1: float | None = None
    s2: float | None = None
    s3: float | None = None

    # Returns
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None

    # Volume
    vol_day: float | None = None
    vol_week: float | None = None
    vol_month: float | None = None

    # Beta
    beta_1m: float | None = None
    beta_3m: float | None = None
    beta_1y: float | None = None
    beta_3y: float | None = None

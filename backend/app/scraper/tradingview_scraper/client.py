from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.scraper.tradingview_scraper.config import DEFAULT_BARS, DEFAULT_EXCHANGE, DEFAULT_INTERVAL
from app.scraper.tradingview_scraper.models import CandleDTO, CandlesResult

logger = logging.getLogger(__name__)

_INTERVAL_TO_DAYS: dict[str, int] = {
    "1": 1,
    "5": 1,
    "15": 1,
    "30": 1,
    "60": 1,
    "120": 1,
    "240": 1,
    "1D": 1,
    "1W": 7,
    "1M": 30,
}


def _estimate_start_date(bars: int, interval: str) -> str:
    days_per_bar = _INTERVAL_TO_DAYS.get(interval, 1)
    buffer = max(bars * days_per_bar + 30, 365)
    start = datetime.now(timezone.utc) - timedelta(days=buffer)
    return start.strftime("%Y-%m-%d")


def get_candles(
    symbol: str,
    exchange: str = DEFAULT_EXCHANGE,
    interval: str = DEFAULT_INTERVAL,
    bars: int = DEFAULT_BARS,
) -> CandlesResult | None:
    """Fetch OHLCV candles from TradingView via TvDatafeed.

    Returns CandlesResult on success, None on failure.
    """
    try:
        from tv_scraper import TvDatafeed
    except ImportError:
        logger.error("tv_scraper package not installed. Install with: pip install tv_scraper_py")
        return None

    try:
        tv = TvDatafeed()
        start_date = _estimate_start_date(bars, interval)
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        df = tv.get(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            interval=interval,
            start=start_date,
            end=end_date,
            output_format="dict",
        )

        if df is None or len(df) == 0:
            return None

        recent = df[-bars:] if len(df) > bars else df

        candles = []
        for bar in recent:
            ts = bar.get("timestamp", 0)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else ""
            candles.append(CandleDTO(
                datetime=dt,
                open=bar.get("open", 0),
                high=bar.get("high", 0),
                low=bar.get("low", 0),
                close=bar.get("close", 0),
                volume=bar.get("volume", 0),
            ))

        return CandlesResult(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            interval=interval,
            candles=candles,
        )
    except Exception as e:
        logger.exception("Failed to fetch candles for %s:%s", exchange, symbol)
        return None

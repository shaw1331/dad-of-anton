from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, float]] = {}
_TTL = 60


def _parse_price(value: str) -> float | None:
    try:
        price = float(value.replace(",", ""))
        return price if price > 0 else None
    except (ValueError, AttributeError):
        return None


def _from_screener(ticker: str) -> float | None:
    try:
        from app.scraper.screener_scraper.stock_scraper import ScreenerStockScraper
    except ImportError:
        return None

    try:
        result = ScreenerStockScraper().get_technical_data(ticker)
        if not result.success or result.data is None:
            return None
        raw = (result.data.data.get("ratios") or {}).get("Current Price") or {}
        value = raw.get("value") if isinstance(raw, dict) else None
        return _parse_price(value) if value else None
    except Exception:
        logger.exception("Screener price fetch failed for %s", ticker)
        return None


def fetch_ltp(ticker: str) -> float | None:
    key = ticker.upper()
    cached = _CACHE.get(key)
    if cached and time.monotonic() - cached[1] < _TTL:
        return cached[0]
    price = _from_screener(key)
    if price is not None:
        _CACHE[key] = (price, time.monotonic())
    return price

from __future__ import annotations

import io
import logging
import time
from typing import Type

import pandas as pd
import requests

from app.nse_screener.exceptions import ConfigError, DataFetchError
from app.nse_screener.interfaces import BaseScreener

logger = logging.getLogger(__name__)

NSE_SYMBOLS_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


class ScreenerFactory:
    """Factory for NSE screener instances.

    Screeners are registered by name. Uses the same classmethod
    pattern as AgentFactory and ScraperFactory.
    """

    _screeners: dict[str, Type[BaseScreener]] = {}

    @classmethod
    def register(cls, name_or_cls: str | Type[BaseScreener]) -> None:
        """Register a screener implementation.

        Can be used as:
            ScreenerFactory.register("name", MyScreener)
            @ScreenerFactory.register
            class MyScreener(BaseScreener): ...
        """
        if isinstance(name_or_cls, str):
            # Called as register("name") — returns a decorator
            def decorator(screener_cls: Type[BaseScreener]) -> Type[BaseScreener]:
                cls._screeners[name_or_cls] = screener_cls
                return screener_cls
            return decorator
        # Called as @register with the class directly
        cls._screeners[name_or_cls.name] = name_or_cls

    @classmethod
    def get(cls, name: str) -> BaseScreener:
        """Get a screener instance by name.

        Raises:
            ConfigError: If no screener is registered for the name.
        """
        screener_cls = cls._screeners.get(name)
        if screener_cls is None:
            available = list(cls._screeners.keys())
            raise ConfigError(
                f"No screener registered for '{name}'. "
                f"Available: {available}"
            )
        return screener_cls()

    @classmethod
    def list_screeners(cls) -> list[dict[str, str]]:
        """Return metadata for all registered screeners."""
        return [
            {"name": name, "description": screener_cls.description}
            for name, screener_cls in cls._screeners.items()
        ]


def fetch_nse_symbols() -> list[str]:
    """Fetch all NSE equity symbols from the official CSV list."""
    try:
        resp = requests.get(NSE_SYMBOLS_URL, headers=NSE_HEADERS, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        col = "SYMBOL" if "SYMBOL" in df.columns else df.columns[0]
        symbols = [str(s).strip().upper() for s in df[col].dropna()]
        if not symbols:
            raise DataFetchError("NSE CSV returned no symbols")
        logger.info("Fetched %d NSE symbols", len(symbols))
        return symbols
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to fetch NSE symbols: {e}") from e


def fetch_stock_data(
    symbols: list[str],
    period: str = "6mo",
    chunk_size: int = 200,
) -> dict[str, pd.DataFrame]:
    """Batch-download daily OHLCV data for NSE stocks via yfinance.

    Args:
        symbols: NSE symbols (without .NS suffix).
        period: History period (e.g. "6mo", "1y").
        chunk_size: Number of tickers per yfinance batch call.

    Returns:
        Dict mapping symbol -> DataFrame with OHLCV columns.
    """
    import yfinance as yf

    tickers = [s + ".NS" for s in symbols]
    out: dict[str, pd.DataFrame] = {}

    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i : i + chunk_size]
        chunk_syms = symbols[i : i + chunk_size]
        try:
            raw = yf.download(
                chunk,
                period=period,
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            for sym, ticker in zip(chunk_syms, chunk):
                try:
                    df = raw[ticker].dropna(how="all") if len(chunk) > 1 else raw.dropna(how="all")
                    if not df.empty:
                        out[sym] = df
                except KeyError:
                    continue
        except Exception as e:
            logger.warning("Failed to download chunk %d-%d: %s", i, i + chunk_size, e)

        if i + chunk_size < len(tickers):
            time.sleep(0.5)

    logger.info("Downloaded data for %d/%d symbols", len(out), len(symbols))
    return out

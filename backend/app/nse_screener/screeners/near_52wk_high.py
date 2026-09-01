from __future__ import annotations

import logging

import pandas as pd

from app.nse_screener.factory import ScreenerFactory, fetch_nse_symbols, fetch_stock_data
from app.nse_screener.interfaces import BaseScreener

logger = logging.getLogger(__name__)


@ScreenerFactory.register
class Near52WeekHigh(BaseScreener):
    """Stocks within 2% of their 52-week high — potential breakout candidates."""

    name = "Near 52W High"
    description = "Stocks within 2% of 52-week high — potential breakouts"

    def run(self) -> list[dict]:
        pct_threshold = 2.0
        min_volume = 100_000

        symbols = fetch_nse_symbols()
        data = fetch_stock_data(symbols, period="1y")

        rows = []
        for sym, df in data.items():
            try:
                df_valid = df.dropna(subset=["Close"])
                if len(df_valid) < 50:
                    continue

                last_price = df_valid["Close"].iloc[-1]
                high_52wk = df_valid["High"].iloc[-252:].max()
                pct_from_high = (high_52wk - last_price) / high_52wk * 100
                avg_volume = df_valid["Volume"].iloc[-20:].mean()

                if pct_from_high > pct_threshold:
                    continue
                if avg_volume < min_volume:
                    continue

                rows.append({
                    "Symbol": sym,
                    "Price": round(float(last_price), 2),
                    "52W High": round(float(high_52wk), 2),
                    "From High%": round(float(pct_from_high), 2),
                    "Avg Volume": int(avg_volume),
                })
            except Exception:
                continue

        rows.sort(key=lambda r: r["From High%"])
        return rows

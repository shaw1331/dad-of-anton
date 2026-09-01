from __future__ import annotations

import logging

import pandas as pd

from app.nse_screener.factory import ScreenerFactory, fetch_nse_symbols, fetch_stock_data
from app.nse_screener.interfaces import BaseScreener

logger = logging.getLogger(__name__)


@ScreenerFactory.register
class VolumeSpike(BaseScreener):
    """Stocks with today's volume > 3x their 20-day average — unusual activity."""

    name = "Volume Spike"
    description = "Stocks with volume > 3x 20-day average — unusual activity"

    def run(self) -> list[dict]:
        volume_multiplier = 3.0
        lookback = 20
        min_volume = 100_000

        symbols = fetch_nse_symbols()
        data = fetch_stock_data(symbols, period="6mo")

        rows = []
        for sym, df in data.items():
            try:
                df_valid = df.dropna(subset=["Close"])
                if len(df_valid) < lookback + 1:
                    continue

                last_price = df_valid["Close"].iloc[-1]
                today_volume = df_valid["Volume"].iloc[-1]
                avg_volume = df_valid["Volume"].iloc[-lookback - 1 : -1].mean()

                if avg_volume < min_volume:
                    continue
                if today_volume < avg_volume * volume_multiplier:
                    continue

                ratio = today_volume / avg_volume
                rows.append({
                    "Symbol": sym,
                    "Price": round(float(last_price), 2),
                    "Vol Ratio": round(float(ratio), 1),
                    "Today Vol": int(today_volume),
                    "Avg Vol": int(avg_volume),
                })
            except Exception:
                continue

        rows.sort(key=lambda r: r["Vol Ratio"], reverse=True)
        return rows

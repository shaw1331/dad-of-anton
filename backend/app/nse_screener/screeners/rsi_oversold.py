from __future__ import annotations

import logging

import pandas as pd

from app.nse_screener.factory import ScreenerFactory, fetch_nse_symbols, fetch_stock_data
from app.nse_screener.interfaces import BaseScreener

logger = logging.getLogger(__name__)


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


@ScreenerFactory.register
class RsiOversold(BaseScreener):
    """Stocks with RSI(14) below 30 — potential oversold bounce candidates."""

    name = "RSI Oversold"
    description = "Stocks with RSI(14) below 30 — potential oversold bounce"

    def run(self) -> list[dict]:
        min_rsi = 30.0
        min_volume = 100_000
        rsi_period = 14

        symbols = fetch_nse_symbols()
        data = fetch_stock_data(symbols, period="6mo")

        rows = []
        for sym, df in data.items():
            try:
                df_valid = df.dropna(subset=["Close"])
                if len(df_valid) < rsi_period + 5:
                    continue

                df_calc = df_valid.copy()
                df_calc["RSI"] = _compute_rsi(df_calc["Close"], rsi_period)
                latest_rsi = df_calc["RSI"].iloc[-1]
                last_price = df_calc["Close"].iloc[-1]
                avg_volume = df_calc["Volume"].iloc[-20:].mean()

                if pd.isna(latest_rsi) or latest_rsi >= min_rsi:
                    continue
                if avg_volume < min_volume:
                    continue

                rows.append({
                    "Symbol": sym,
                    "Price": round(float(last_price), 2),
                    "RSI": round(float(latest_rsi), 1),
                    "Avg Volume": int(avg_volume),
                })
            except Exception:
                continue

        rows.sort(key=lambda r: r["RSI"])
        return rows

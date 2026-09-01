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
class MomentumRunner(BaseScreener):
    """Stocks with >5% price move in the last 2 trading sessions."""

    name = "Momentum Runner"
    description = "Stocks with >5% price move in the last 2 trading sessions"

    def run(self) -> list[dict]:
        lookback = 2
        min_pct = 5.0
        min_volume = 100_000

        symbols = fetch_nse_symbols()
        data = fetch_stock_data(symbols, period="6mo")

        rows = []
        for sym, df in data.items():
            try:
                df_valid = df.dropna(subset=["Close"])
                if len(df_valid) < lookback:
                    continue

                window = df_valid.iloc[-lookback:]
                start_price = window["Close"].iloc[0]
                last_price = df_valid["Close"].iloc[-1]
                pct_change = (last_price - start_price) / start_price * 100
                avg_volume = window["Volume"].mean()

                if abs(pct_change) < min_pct:
                    continue
                if avg_volume < min_volume:
                    continue

                rows.append({
                    "Symbol": sym,
                    "Price": round(float(last_price), 2),
                    "Chg%": round(float(pct_change), 2),
                    "Avg Volume": int(avg_volume),
                })
            except Exception:
                continue

        rows.sort(key=lambda r: abs(r["Chg%"]), reverse=True)
        return rows

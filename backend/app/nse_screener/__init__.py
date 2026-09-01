from __future__ import annotations

# Auto-register all screeners by importing the screeners package.
# Each screener module uses @ScreenerFactory.register at import time.
from app.nse_screener.screeners import momentum, rsi_oversold, volume_spike, near_52wk_high  # noqa: F401

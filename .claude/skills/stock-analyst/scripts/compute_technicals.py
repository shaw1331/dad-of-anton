"""Compute technical indicators + graded signals from prices.csv.

Usage: compute_technicals.py TICKER
Signals are in {-1, -0.5, 0, +0.5, +1}. Signal rules follow references/evidence.md:
52w-high proximity is continuation-scored (George & Hwang 2004); RSI extremes are
conditioned on trend and 52w position (short-term reversal is conditional).

Exit codes: 0 ok · 2 prices.csv missing/unreadable
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from _bootstrap import out_dir, write_json


def sig(value: float) -> float:
    return float(value)


def compute(df: pd.DataFrame) -> tuple[dict, dict, list[str]]:
    warnings: list[str] = []
    close, high, low, vol = df["Close"], df["High"], df["Low"], df["Volume"]
    price = float(close.iloc[-1])
    ind: dict[str, dict] = {}

    def add(name: str, value, signal: float | None, detail: str) -> None:
        ind[name] = {"value": value, "signal": signal, "detail": detail}

    # --- Moving averages ---
    smas: dict[int, float | None] = {}
    for n in (20, 50, 200):
        if len(close) >= n:
            sma = float(close.rolling(n).mean().iloc[-1])
            smas[n] = sma
            pct = (price / sma - 1) * 100
            s = 0.0 if abs(pct) < 1 else (1.0 if pct > 0 else -1.0)
            add(f"price_vs_sma{n}", round(sma, 2), sig(s), f"price {pct:+.1f}% vs SMA{n} {sma:.2f}")
        else:
            smas[n] = None
            add(f"price_vs_sma{n}", None, None, f"insufficient history for SMA{n}")
            warnings.append(f"SMA{n} unavailable ({len(close)} rows)")

    # --- Trend cross state (50 vs 200) ---
    if smas[50] is not None and smas[200] is not None:
        sma50_series = close.rolling(50).mean()
        sma200_series = close.rolling(200).mean()
        state = 1.0 if smas[50] > smas[200] else -1.0
        diff = (sma50_series - sma200_series).dropna()
        recent_cross = bool(len(diff) > 20 and (np.sign(diff.iloc[-20:]) != np.sign(diff.iloc[-1])).any())
        label = "golden" if state > 0 else "death"
        add("trend_cross", label, sig(state),
            f"{label} cross state (SMA50 {'>' if state > 0 else '<'} SMA200)"
            + ("; crossed within last 20 sessions" if recent_cross else ""))
    else:
        add("trend_cross", None, None, "needs 200 bars")

    # --- 52-week range position (continuation-scored) ---
    lookback = min(len(close), 252)
    hi52 = float(high.iloc[-lookback:].max())
    lo52 = float(low.iloc[-lookback:].min())
    off_high = (1 - price / hi52) * 100  # % below 52w high
    above_low = (price / lo52 - 1) * 100
    near_high = off_high <= 10
    if off_high <= 5:
        s52 = 1.0
    elif off_high <= 15:
        s52 = 0.5
    elif above_low <= 10:
        s52 = -1.0
    elif above_low <= 25:
        s52 = -0.5
    else:
        s52 = 0.0
    add("position_52w", {"high": round(hi52, 2), "low": round(lo52, 2)}, sig(s52),
        f"{off_high:.1f}% below 52w high, {above_low:.1f}% above 52w low")

    # --- RSI(14), Wilder smoothing; extremes conditioned on trend/52w position ---
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = float((100 - 100 / (1 + rs)).iloc[-1])
    above_sma200 = smas[200] is not None and price > smas[200]
    if rsi >= 70:
        s_rsi, note = (0.0, "overbought but near 52w high — continuation regime") if near_high else (-1.0, "overbought")
    elif rsi >= 60:
        s_rsi, note = 0.5, "bullish momentum zone"
    elif rsi > 40:
        s_rsi, note = 0.0, "neutral zone"
    elif rsi > 30:
        s_rsi, note = -0.5, "weak momentum"
    else:
        s_rsi, note = (0.5, "oversold above SMA200 — bounce candidate") if above_sma200 else (-0.5, "oversold in downtrend")
    add("rsi14", round(rsi, 1), sig(s_rsi), f"RSI {rsi:.1f}: {note}")

    # --- MACD (12, 26, 9) ---
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal_line
    hist_rising = bool(hist.iloc[-1] > hist.iloc[-5])
    if macd_line.iloc[-1] > signal_line.iloc[-1]:
        s_macd = 1.0 if hist_rising else 0.5
        note = "line above signal" + (", histogram rising" if hist_rising else ", histogram fading")
    else:
        s_macd = -1.0 if not hist_rising else -0.5
        note = "line below signal" + (", histogram falling" if not hist_rising else ", histogram recovering")
    add("macd", {"line": round(float(macd_line.iloc[-1]), 2), "signal": round(float(signal_line.iloc[-1]), 2)},
        sig(s_macd), f"MACD {note}")

    # --- Volume (direction-aware, 5d vs 20d average) ---
    if len(vol.dropna()) >= 20 and float(vol.iloc[-20:].mean()) > 0:
        ratio = float(vol.iloc[-5:].mean() / vol.iloc[-20:].mean())
        chg5 = float(close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 6 else 0.0
        if ratio > 1.3:
            s_vol = 1.0 if chg5 > 0 else -1.0
            note = f"volume surge x{ratio:.2f} on {'+' if chg5 > 0 else ''}{chg5:.1f}% 5d move"
        else:
            s_vol, note = 0.0, f"volume normal (x{ratio:.2f} vs 20d avg)"
        add("volume_trend", round(ratio, 2), sig(s_vol), note)
    else:
        add("volume_trend", None, None, "volume data unavailable")

    # --- Momentum returns (3/6/12 months ≈ 63/126/252 sessions) ---
    for name, bars in (("momentum_3m", 63), ("momentum_6m", 126), ("momentum_12m", 252)):
        if len(close) > bars:
            r = float(close.iloc[-1] / close.iloc[-1 - bars] - 1) * 100
            s = 0.0 if abs(r) < 5 else (0.5 if r > 0 else -0.5) if abs(r) < 15 else (1.0 if r > 0 else -1.0)
            add(name, round(r, 1), sig(s), f"{r:+.1f}% over ~{bars} sessions")
        else:
            add(name, None, None, "insufficient history")

    # --- ATR(14) volatility context (not directional) ---
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1])
    add("atr14_pct", round(atr / price * 100, 2), None, f"ATR {atr:.2f} ({atr / price * 100:.1f}% of price) — volatility context")

    # --- Support / resistance from 12m swing points ---
    win = 10
    recent_high = high.iloc[-252:]
    recent_low = low.iloc[-252:]
    swing_highs = recent_high[recent_high == recent_high.rolling(2 * win + 1, center=True).max()].dropna()
    swing_lows = recent_low[recent_low == recent_low.rolling(2 * win + 1, center=True).min()].dropna()

    def cluster(levels: list[float]) -> list[float]:
        out: list[float] = []
        for lv in sorted(levels):
            if out and abs(lv / out[-1] - 1) < 0.02:
                out[-1] = (out[-1] + lv) / 2
            else:
                out.append(lv)
        return out

    supports = [lv for lv in cluster(list(swing_lows)) if lv < price][-2:]
    resistances = [lv for lv in cluster(list(swing_highs)) if lv > price][:2]
    if supports and (price / supports[-1] - 1) * 100 <= 3:
        s_sr, note = 0.5, f"price within 3% of support {supports[-1]:.2f}"
    elif resistances and (resistances[0] / price - 1) * 100 <= 2:
        s_sr, note = -0.5, f"resistance {resistances[0]:.2f} within 2% overhead"
    else:
        s_sr, note = 0.0, "no immediate S/R level in play"
    add("support_resistance",
        {"supports": [round(s, 2) for s in supports], "resistances": [round(r, 2) for r in resistances]},
        sig(s_sr), note)

    # --- Invalidation level candidates ---
    nearest_support = supports[-1] if supports else (smas[20] or price * 0.95)
    nearest_resistance = resistances[0] if resistances else (smas[20] or price * 1.05)
    levels = {
        "price": round(price, 2),
        "st_bull_invalidation": round(min(nearest_support, smas[20] or nearest_support) - 1.5 * atr, 2),
        "st_bear_invalidation": round(max(nearest_resistance, smas[20] or nearest_resistance) + 1.5 * atr, 2),
        "lt_invalidation": round(smas[200], 2) if smas[200] else None,
    }
    return ind, levels, warnings


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: compute_technicals.py TICKER")
        return 1
    ticker = sys.argv[1].upper()
    odir = out_dir(ticker)
    csv_path = odir / "prices.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found — run fetch_prices.py first")
        return 2

    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    if df.empty or "Close" not in df.columns:
        print("ERROR: prices.csv is empty or malformed")
        return 2

    ind, levels, warnings = compute(df)
    write_json(odir / "technicals.json", ticker, {
        "as_of": str(df.index[-1].date()),
        "indicators": ind,
        "levels": levels,
    }, warnings)

    print(f"{ticker} technicals as of {df.index[-1].date()} (close {levels['price']}):")
    for name, d in ind.items():
        s = d["signal"]
        tag = "n/a" if s is None else f"{s:+.1f}"
        print(f"  {name:<20} [{tag:>4}] {d['detail']}")
    print(f"  levels: {levels}")
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import statistics
from typing import Any

from pydantic import BaseModel


class VolumeMetrics(BaseModel):
    avg_volume_10d: float
    avg_volume_20d: float
    current_volume: float
    volume_spike: bool
    volume_trend: str


class CalculatedLevels(BaseModel):
    recommendation: str
    conviction: str
    entry_above: float | None = None
    stop_loss: float | None = None
    targets: list[float]
    level_reasoning: str
    volume_metrics: VolumeMetrics | None = None


def _compute_volume(candles: list[dict]) -> VolumeMetrics | None:
    if not candles or len(candles) < 5:
        return None
    volumes = [c["volume"] for c in candles if c.get("volume")]
    if not volumes:
        return None
    current = volumes[-1]
    avg_10 = statistics.mean(volumes[-10:]) if len(volumes) >= 10 else statistics.mean(volumes)
    avg_20 = statistics.mean(volumes[-20:]) if len(volumes) >= 20 else avg_10
    spike = current > 1.5 * avg_10 if avg_10 > 0 else False
    if len(volumes) >= 5:
        recent = volumes[-5:]
        slope = (recent[-1] - recent[0]) / len(recent) if recent[0] > 0 else 0
        trend = "increasing" if slope > 0.05 * recent[0] else ("decreasing" if slope < -0.05 * recent[0] else "flat")
    else:
        trend = "flat"
    return VolumeMetrics(
        avg_volume_10d=round(avg_10, 0),
        avg_volume_20d=round(avg_20, 0),
        current_volume=round(current, 0),
        volume_spike=spike,
        volume_trend=trend,
    )


def _high_volume_breakout(candles: list[dict], price: float | None, s1: float | None, r1: float | None) -> bool:
    if not candles or len(candles) < 11 or price is None:
        return False
    closes = [c["close"] for c in candles[-11:] if c.get("close")]
    if len(closes) < 11:
        return False
    prev_high = max(closes[:-1])
    volumes = [c["volume"] for c in candles[-11:] if c.get("volume")]
    avg_vol = statistics.mean(volumes[:-1]) if len(volumes) >= 11 else 1
    return closes[-1] > prev_high and volumes[-1] > 1.5 * avg_vol


def _pick_level(a: float | None, b: float | None, pick_higher: bool) -> float | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b) if pick_higher else min(a, b)


def compute_levels(tl_data: dict, candles: list[dict]) -> CalculatedLevels:
    price = tl_data.get("price")
    if price is None:
        closes = [c["close"] for c in candles if c.get("close")]
        price = closes[-1] if closes else None

    ema_20 = tl_data.get("ema_20")
    ema_50 = tl_data.get("ema_50")
    ema_200 = tl_data.get("ema_200")
    rsi = tl_data.get("rsi")
    adx = tl_data.get("adx")
    pivot = tl_data.get("pivot")
    r1 = tl_data.get("r1")
    r2 = tl_data.get("r2")
    s1 = tl_data.get("s1")
    s2 = tl_data.get("s2")
    atr = tl_data.get("atr")

    vm = _compute_volume(candles)
    hvb = _high_volume_breakout(candles, price, s1, r1)

    bullish_ma = price is not None and ema_20 is not None and ema_50 is not None and ema_200 is not None and price > ema_20 > ema_50 > ema_200
    bearish_ma = price is not None and ema_20 is not None and ema_50 is not None and price < ema_20 < ema_50
    rsi_overbought = rsi is not None and rsi > 70
    rsi_oversold = rsi is not None and rsi < 30
    adx_strong = adx is not None and adx > 25

    score = 0
    reasons = []

    if bullish_ma:
        score += 3
        reasons.append("bullish EMA alignment (price > EMA20 > EMA50 > EMA200)")
    elif bearish_ma:
        score -= 3
        reasons.append("bearish EMA alignment (price < EMA20 < EMA50)")
    else:
        score += 0

    if rsi is not None:
        if 40 <= rsi <= 60:
            score += 1
            reasons.append(f"RSI {rsi:.0f} in neutral zone")
        elif rsi_overbought:
            score -= 2
            reasons.append(f"RSI {rsi:.0f} overbought")
        elif rsi_oversold:
            score += 1
            reasons.append(f"RSI {rsi:.0f} oversold — potential reversal")

    if adx is not None:
        if adx_strong:
            score += 1 if score >= 0 else -1
            reasons.append(f"ADX {adx:.0f} trending market")
        else:
            score += 0
            reasons.append(f"ADX {adx:.0f} weak trend")

    if hvb:
        score += 2
        reasons.append("high volume breakout above resistance")

    if vm and vm.volume_spike:
        score += 1 if score >= 0 else -1
        reasons.append("volume spike confirms conviction")

    if pivot is not None and price is not None:
        if price > pivot and score >= 0:
            score += 1
        elif price < pivot and score < 0:
            score -= 1

    entry = None
    sl = None
    targets = []
    rec = "HOLD"
    conviction = "HOLD"

    if score >= 4:
        rec = "BUY"
        if hvb:
            conviction = "STRONG_BUY"
            entry = max(pivot or price, price or 0) if pivot else price
            targets = [r for r in [r1, r2] if r is not None]
            sl = _pick_level(ema_20, s1, pick_higher=True)
        elif adx_strong and rsi is not None and 45 <= rsi <= 65:
            conviction = "STRONG_BUY"
            entry = price
            targets = [r for r in [r1, r2] if r is not None]
            sl = _pick_level(ema_20, s1, pick_higher=False)
        else:
            conviction = "BUY"
            entry = price
            targets = [r for r in [r1, r2] if r is not None]
            sl = _pick_level(ema_20, s1, pick_higher=True)
    elif 2 <= score < 4:
        rec = "BUY"
        conviction = "CAUTIOUS_BUY"
        entry = price
        targets = [r for r in [pivot, r1] if r is not None]
        sl = _pick_level(ema_20, s1, pick_higher=True) or below_ema20(tl_data, price)
    elif -2 <= score < 2:
        rec = "HOLD"
        conviction = "HOLD"
        entry = None
        sl = None
        targets = []
    elif -4 <= score < -2:
        rec = "SELL"
        conviction = "SELL"
        entry = price
        targets = [s for s in [s1, s2] if s is not None]
        sl = _pick_level(ema_20, pivot, pick_higher=True) or pivot
    else:
        rec = "SELL"
        conviction = "STRONG_SELL"
        entry = price
        targets = [s for s in [s1, s2] if s is not None]
        sl = _pick_level(ema_20, pivot, pick_higher=True) or pivot

    if sl is None and atr is not None and entry is not None:
        sl = round(entry - 2 * atr, 2)
        reasons.append(f"SL set at 2x ATR ({sl})")

    if entry is not None and (rec == "BUY" or conviction in ("BUY", "STRONG_BUY", "CAUTIOUS_BUY")):
        sl_for_reason = sl
        if atr and entry:
            risk = round((entry - sl_for_reason) / entry * 100, 1) if sl_for_reason else None
            risk_str = f", risk {risk}%" if risk else ""
            rw_str = ", ".join([f"R{i+1}={t}" for i, t in enumerate(targets)]) if targets else ""
            reasons.append(f"Entry {entry}, SL {sl_for_reason}{risk_str}, targets {rw_str}")

    return CalculatedLevels(
        recommendation=rec,
        conviction=conviction,
        entry_above=round(entry, 2) if entry else None,
        stop_loss=round(sl, 2) if sl else None,
        targets=[round(t, 2) for t in targets if t is not None],
        level_reasoning="; ".join(reasons) if reasons else "Insufficient data for conviction.",
        volume_metrics=vm,
    )


def below_ema20(tl_data: dict, price: float | None) -> float | None:
    ema_20 = tl_data.get("ema_20")
    if ema_20 and price:
        return round(min(ema_20, price * 0.95), 2)
    return None
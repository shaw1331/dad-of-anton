"""Combine fundamentals + technicals + news into per-horizon scores.

Usage: score.py TICKER
Reads analysis-out/<T>/{fundamentals,technicals,news}.json → writes scores.json.

WEIGHTS is the source of truth for the scoring model (mirrored as a table in
SKILL.md; calibration rationale in references/evidence.md). Missing signals drop
out of both numerator and denominator — the model never fabricates a reading.

Exit codes: 0 ok · 2 required inputs missing (needs at least one of fundamentals/technicals)
"""

from __future__ import annotations

import sys

from _bootstrap import out_dir, read_json, write_json

# signal -> (short-term weight, long-term weight)
WEIGHTS: dict[str, tuple[float, float]] = {
    # technicals (signal values read from technicals.json)
    "price_vs_sma20": (8, 0),
    "price_vs_sma50": (6, 2),
    "price_vs_sma200": (4, 6),
    "trend_cross": (5, 5),
    "rsi14": (5, 2),
    "macd": (8, 2),
    "position_52w": (7, 6),        # 52w-high continuation effect (George & Hwang 2004)
    "volume_trend": (5, 1),
    "momentum_3m": (6, 2),
    "momentum_6m": (4, 5),         # 3-9m momentum validated for India
    "momentum_12m": (0, 5),
    "support_resistance": (5, 0),
    # fundamentals (directions derived below)
    "pe_vs_peers": (2, 8),         # quality-gated (value-trap guard)
    "roe": (1, 8),
    "roce": (1, 8),
    "sales_growth": (2, 8),
    "profit_growth": (2, 8),
    "earnings_surprise": (6, 5),   # PEAD proxy: latest-qtr YoY direction
    "promoter_delta": (2, 6),      # +1 both horizons for small caps (insider effect strongest there)
    "fii_delta": (4, 5),           # FII flows are a documented momentum driver in India
    "dii_delta": (2, 3),
    "dividend_yield": (0, 2),
}
NEWS_CAP = 15
NEWS_PSEUDO_WEIGHT = 15  # counts toward completeness
SMALL_CAP_CR = 20_000

def verdict_for(score: float) -> str:
    if score >= 50:
        return "Strong Bullish"
    if score >= 20:
        return "Bullish"
    if score > -20:
        return "Neutral"
    if score > -50:
        return "Bearish"
    return "Strong Bearish"


def grade(value: float | None, bands: list[tuple[float, float]]) -> float | None:
    """bands = [(threshold, direction), ...] descending; first threshold value >= wins."""
    if value is None:
        return None
    for threshold, direction in bands:
        if value >= threshold:
            return direction
    return bands[-1][1]


def fundamental_signals(f: dict | None) -> dict[str, tuple[float | None, str]]:
    """signal -> (direction, evidence string)."""
    if not f:
        return {}
    d = f.get("derived", {})
    latest = d.get("latest_qtr", {})
    deltas = d.get("shareholding_delta_4q_pp", {})
    out: dict[str, tuple[float | None, str]] = {}

    quality_bands = [(20, 1.0), (15, 0.5), (10, 0.0), (5, -0.5), (-1000, -1.0)]
    out["roe"] = (grade(d.get("roe_pct"), quality_bands), f"ROE {d.get('roe_pct')}%")
    out["roce"] = (grade(d.get("roce_pct"), quality_bands), f"ROCE {d.get('roce_pct')}%")

    growth_bands = [(15, 1.0), (10, 0.5), (0, 0.0), (-1000, -1.0)]
    out["sales_growth"] = (grade(d.get("sales_cagr_3y_pct"), growth_bands), f"3y sales CAGR {d.get('sales_cagr_3y_pct')}%")
    out["profit_growth"] = (grade(d.get("profit_cagr_3y_pct"), growth_bands), f"3y profit CAGR {d.get('profit_cagr_3y_pct')}%")

    surprise_bands = [(15, 1.0), (5, 0.5), (-5, 0.0), (-15, -0.5), (-1000, -1.0)]
    out["earnings_surprise"] = (
        grade(latest.get("net_profit_yoy_pct"), surprise_bands),
        f"latest qtr ({latest.get('period')}) net profit YoY {latest.get('net_profit_yoy_pct')}%, sales YoY {latest.get('sales_yoy_pct')}%",
    )

    pe, med = d.get("stock_pe"), d.get("peer_median_pe")
    if pe is not None and med:
        ratio = pe / med
        quality = (d.get("roe_pct") or 0) >= 15 or (d.get("roce_pct") or 0) >= 15
        if ratio <= 0.8:
            direction = 1.0 if quality else 0.0  # cheap without quality = value-trap risk
            gate = "" if quality else " (quality gate: cheap but ROE/ROCE <15% — no credit)"
        elif ratio <= 1.3:
            direction, gate = 0.0, ""
        elif ratio <= 1.8:
            direction, gate = -0.5, ""
        else:
            direction, gate = -1.0, ""
        out["pe_vs_peers"] = (direction, f"P/E {pe} vs peer median {med} (x{ratio:.2f}){gate}")
    else:
        out["pe_vs_peers"] = (None, "P/E or peer median unavailable")

    delta_bands = [(1.0, 1.0), (0.3, 0.5), (-0.3, 0.0), (-1.0, -0.5), (-1000, -1.0)]
    for signal, cat in (("promoter_delta", "Promoters"), ("fii_delta", "FIIs"), ("dii_delta", "DIIs")):
        out[signal] = (grade(deltas.get(cat), delta_bands), f"{cat} holding {deltas.get(cat):+}pp over 4 qtrs" if deltas.get(cat) is not None else f"{cat} trend unavailable")

    out["dividend_yield"] = (grade(d.get("dividend_yield_pct"), [(2, 1.0), (1, 0.5), (-1000, 0.0)]), f"dividend yield {d.get('dividend_yield_pct')}%")
    return out


def news_points(news: dict | None, horizon: str) -> tuple[float, int]:
    if not news:
        return 0.0, 0
    items = [i for i in news.get("items", []) if i.get("horizon", "both") in (horizon, "both")]
    total = 0.0
    for item in items:
        sign = {"bullish": 1, "bearish": -1}.get(item.get("direction"), 0)
        total += sign * float(item.get("impact", 1)) * 2.5
    return max(-NEWS_CAP, min(NEWS_CAP, total)), len(items)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: score.py TICKER")
        return 1
    ticker = sys.argv[1].upper()
    odir = out_dir(ticker)

    fundamentals = read_json(odir / "fundamentals.json")
    technicals = read_json(odir / "technicals.json")
    news = read_json(odir / "news.json")

    if not fundamentals and not technicals:
        print("ERROR: neither fundamentals.json nor technicals.json present — run the fetch scripts first")
        return 2

    weights = dict(WEIGHTS)
    mcap = (fundamentals or {}).get("derived", {}).get("market_cap_cr")
    small_cap = mcap is not None and mcap < SMALL_CAP_CR
    if small_cap:
        st, lt = weights["promoter_delta"]
        weights["promoter_delta"] = (st + 1, lt + 1)

    # Collect (direction, evidence) per signal
    readings: dict[str, tuple[float | None, str]] = {}
    tech_ind = (technicals or {}).get("indicators", {})
    for name in weights:
        if name in tech_ind:
            readings[name] = (tech_ind[name].get("signal"), tech_ind[name].get("detail", ""))
    readings.update(fundamental_signals(fundamentals))

    horizons = {}
    contributions = []
    for h_idx, horizon in ((0, "short_term"), (1, "long_term")):
        num = gross = avail_w = total_w = 0.0
        h_key = "short" if horizon == "short_term" else "long"
        h_rows = []
        for name, (st_w, lt_w) in weights.items():
            w = (st_w, lt_w)[h_idx]
            total_w += w
            if w == 0:
                continue
            direction, evidence = readings.get(name, (None, "not computed"))
            h_rows.append({"horizon": horizon, "signal": name, "direction": direction, "weight": w, "evidence": evidence})
            if direction is None:
                continue
            avail_w += w
            num += direction * w
            gross += abs(direction) * w

        for row in h_rows:
            row["points"] = (round(100 * row["direction"] * row["weight"] / avail_w, 1)
                             if row["direction"] is not None and avail_w else None)
        contributions.extend(h_rows)

        base = 100 * num / avail_w if avail_w else 0.0
        n_points, n_items = news_points(news, h_key)
        score = max(-100.0, min(100.0, base + n_points))

        agreement = abs(num) / gross if gross else 0.0
        completeness = (avail_w + (NEWS_PSEUDO_WEIGHT if news is not None else 0)) / (total_w + NEWS_PSEUDO_WEIGHT)
        confidence = 0.6 * agreement + 0.4 * completeness
        conf_band = "Low" if confidence < 0.45 else ("Medium" if confidence <= 0.70 else "High")

        verdict = verdict_for(score)
        levels = (technicals or {}).get("levels", {})
        if horizon == "short_term":
            if not technicals:
                verdict, invalidation = "Insufficient data", "no price data available"
            elif score >= 20:
                invalidation = f"daily close below {levels.get('st_bull_invalidation')}"
            elif score <= -20:
                invalidation = f"daily close above {levels.get('st_bear_invalidation')}"
            else:
                invalidation = f"breakout beyond {levels.get('st_bull_invalidation')} / {levels.get('st_bear_invalidation')} range"
        else:
            lt_level = levels.get("lt_invalidation")
            parts = []
            if lt_level:
                parts.append(f"sustained close {'below' if score >= 0 else 'above'} SMA200 ({lt_level})")
            parts.append("2 consecutive quarters of YoY profit decline" if score >= 0 else "2 consecutive quarters of YoY profit growth")
            parts.append("promoter stake drop >1pp" if score >= 0 else "promoter stake rise >1pp")
            invalidation = "; ".join(parts)

        horizons[horizon] = {
            "score": round(score, 1),
            "base_score": round(base, 1),
            "news_points": round(n_points, 1),
            "news_items_considered": n_items,
            "verdict": verdict,
            "confidence": {"value": round(confidence, 2), "band": conf_band,
                           "agreement": round(agreement, 2), "completeness": round(completeness, 2)},
            "invalidation": invalidation,
        }

    # Cross-source sanity check
    warnings = []
    scr_price = (fundamentals or {}).get("derived", {}).get("current_price")
    yf_price = (technicals or {}).get("levels", {}).get("price")
    if scr_price and yf_price and abs(scr_price / yf_price - 1) > 0.05:
        warnings.append(f"screener price {scr_price} vs yfinance close {yf_price} differ >5% — check ticker mapping")
    if news is None:
        warnings.append("news.json absent — news contribution 0, completeness reduced")

    write_json(odir / "scores.json", ticker, {
        "small_cap_promoter_amplifier": small_cap,
        "horizons": horizons,
        "contributions": contributions,
        "weights_used": {k: {"st": v[0], "lt": v[1]} for k, v in weights.items()},
    }, warnings)

    for horizon, h in horizons.items():
        print(f"{ticker} {horizon}: {h['verdict']} ({h['score']:+.1f}/100, base {h['base_score']:+.1f}, "
              f"news {h['news_points']:+.1f}) confidence {h['confidence']['band']} ({h['confidence']['value']})")
        print(f"  invalidation: {h['invalidation']}")
        ranked = sorted((c for c in contributions if c["horizon"] == horizon and c["direction"]),
                        key=lambda c: abs(c["direction"] * c["weight"]), reverse=True)[:5]
        for c in ranked:
            print(f"  {'+' if c['direction'] > 0 else '-'} {c['signal']} (dir {c['direction']:+.1f} × w {c['weight']}): {c['evidence']}")
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

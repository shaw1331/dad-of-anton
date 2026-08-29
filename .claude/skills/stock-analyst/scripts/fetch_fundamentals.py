"""Fetch fundamentals for a ticker from screener.in into fundamentals.json.

Usage: fetch_fundamentals.py TICKER [--fresh]
Exit codes: 0 ok (or cached) · 2 ticker not found · 3 partial data (written with warnings)
"""

from __future__ import annotations

import statistics
import sys

from _bootstrap import is_fresh, out_dir, parse_numeric, read_json, write_json
from extractors import (
    extract_annual_pl,
    extract_peers,
    extract_quarters_history,
    extract_ranges,
    extract_shareholding_trend,
)
from config import BASE_URL
from scrape_companies import extract_company_data
from utils import get_page


def yoy_from_history(history: dict | None, row_name: str) -> tuple[str | None, float | None]:
    """Latest period value and YoY % change (vs 4 periods earlier) for a quarters row."""
    if not history:
        return None, None
    values = history["rows"].get(row_name)
    if not values or len(values) < 5:
        return None, None
    latest, prior = parse_numeric(values[-1]), parse_numeric(values[-5])
    if latest is None or prior is None or prior == 0:
        return history["periods"][-1] if history["periods"] else None, None
    return history["periods"][-1], round((latest - prior) / abs(prior) * 100, 1)


def shareholding_delta(history: dict | None, category: str, quarters_back: int = 4) -> float | None:
    if not history:
        return None
    values = history["rows"].get(category)
    if not values:
        return None
    latest = parse_numeric(values[-1])
    base_idx = -1 - quarters_back if len(values) > quarters_back else 0
    base = parse_numeric(values[base_idx])
    if latest is None or base is None:
        return None
    return round(latest - base, 2)


def peer_median_pe(peers: dict | None) -> float | None:
    if not peers or not peers.get("headers"):
        return None
    try:
        pe_idx = next(i for i, h in enumerate(peers["headers"]) if "P/E" in h)
    except StopIteration:
        return None
    values = []
    for row in peers["rows"]:
        if len(row) > pe_idx and not row[0].lower().startswith("median"):
            v = parse_numeric(row[pe_idx])
            if v is not None and v > 0:
                values.append(v)
    return round(statistics.median(values), 1) if values else None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_fundamentals.py TICKER [--fresh]")
        return 1
    ticker = sys.argv[1].upper()
    fresh = "--fresh" in sys.argv
    odir = out_dir(ticker)
    out_path = odir / "fundamentals.json"

    if not fresh and is_fresh(out_path):
        cached = read_json(out_path)
        print(f"[cached] {ticker}: {cached.get('company_name')} — fundamentals from {cached['fetched_at'][:10]}")
        return 0

    soup, source_url = None, None
    for variant in (f"{BASE_URL}/company/{ticker}/consolidated/", f"{BASE_URL}/company/{ticker}/"):
        soup = get_page(variant)
        if soup is not None and soup.select_one("#top-ratios"):
            source_url = variant
            break
        soup = None

    if soup is None:
        print(f"ERROR: '{ticker}' not found on screener.in (tried consolidated and standalone URLs)")
        return 2

    warnings: list[str] = []
    ratios = extract_company_data(soup)

    quarters = extract_quarters_history(soup)
    annual = extract_annual_pl(soup)
    shareholding = extract_shareholding_trend(soup)
    ranges = extract_ranges(soup)
    peers, peers_warning = extract_peers(soup)

    for name, obj in (("quarters", quarters), ("annual P&L", annual), ("shareholding", shareholding)):
        if not obj:
            warnings.append(f"{name} table missing")
    if peers_warning:
        warnings.append(peers_warning)

    latest_qtr_period, sales_yoy = yoy_from_history(quarters, "Sales")
    _, profit_yoy = yoy_from_history(quarters, "Net Profit")

    derived = {
        "market_cap_cr": parse_numeric(ratios.get("Market Cap")),
        "current_price": parse_numeric(ratios.get("Current Price")),
        "stock_pe": parse_numeric(ratios.get("Stock P/E")),
        "roe_pct": parse_numeric(ratios.get("ROE")),
        "roce_pct": parse_numeric(ratios.get("ROCE")),
        "dividend_yield_pct": parse_numeric(ratios.get("Dividend Yield")),
        "latest_qtr": {"period": latest_qtr_period, "sales_yoy_pct": sales_yoy, "net_profit_yoy_pct": profit_yoy},
        "sales_cagr_3y_pct": parse_numeric(ranges.get("Compounded Sales Growth", {}).get("3 Years")),
        "profit_cagr_3y_pct": parse_numeric(ranges.get("Compounded Profit Growth", {}).get("3 Years")),
        "roe_3y_pct": parse_numeric(ranges.get("Return on Equity", {}).get("3 Years")),
        "shareholding_delta_4q_pp": {
            cat: shareholding_delta(shareholding, cat)
            for cat in ("Promoters", "FIIs", "DIIs", "Public")
        },
        "peer_median_pe": peer_median_pe(peers),
    }

    write_json(out_path, ticker, {
        "company_name": ratios.get("Company Name", ticker),
        "source_url": source_url,
        "ratios": ratios,
        "quarters": quarters,
        "annual": annual,
        "shareholding": shareholding,
        "ranges": ranges,
        "peers": peers,
        "derived": derived,
    }, warnings)

    d = derived
    print(f"{ratios.get('Company Name', ticker)} ({ticker}) — {source_url}")
    print(f"  MCap ₹{d['market_cap_cr']} Cr · CMP {d['current_price']} · P/E {d['stock_pe']}"
          f" (peer median {d['peer_median_pe']}) · ROE {d['roe_pct']}% · ROCE {d['roce_pct']}%")
    print(f"  Latest qtr {d['latest_qtr']['period']}: sales YoY {d['latest_qtr']['sales_yoy_pct']}%,"
          f" net profit YoY {d['latest_qtr']['net_profit_yoy_pct']}%")
    print(f"  3y CAGR: sales {d['sales_cagr_3y_pct']}%, profit {d['profit_cagr_3y_pct']}%")
    print(f"  Shareholding Δ4q (pp): {d['shareholding_delta_4q_pp']}")
    if ratios.get("Pros"):
        print(f"  Pros: {ratios['Pros'][:150]}")
    if ratios.get("Cons"):
        print(f"  Cons: {ratios['Cons'][:150]}")
    for w in warnings:
        print(f"WARNING: {w}")
    return 3 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())

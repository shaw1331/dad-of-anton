"""Fetch 2y daily adjusted OHLCV for <TICKER>.NS via yfinance.

Usage: fetch_prices.py TICKER [--fresh]
Exit codes: 0 ok (or cached) · 2 no data (bad ticker on Yahoo) · 3 short history (<200 rows, still written)
"""

from __future__ import annotations

import sys

from _bootstrap import is_fresh, out_dir, read_json, write_json


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_prices.py TICKER [--fresh]")
        return 1
    ticker = sys.argv[1].upper()
    fresh = "--fresh" in sys.argv

    odir = out_dir(ticker)
    csv_path = odir / "prices.csv"
    meta_path = odir / "prices_meta.json"

    if not fresh and csv_path.exists() and is_fresh(meta_path):
        meta = read_json(meta_path)
        print(f"[cached] {ticker}: {meta['rows']} rows through {meta['last_date']}, last close {meta['last_close']}")
        return 0

    import yfinance as yf

    symbol = f"{ticker}.NS"
    df = yf.download(symbol, period="2y", interval="1d", auto_adjust=True, progress=False)

    if df is None or df.empty:
        print(f"ERROR: no price data for {symbol} on Yahoo Finance (bad/unlisted ticker?)")
        return 2

    # yfinance returns MultiIndex columns (field, symbol) — flatten to plain field names
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = [c[0] for c in df.columns]
    df = df[[c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]]
    df = df.dropna(subset=["Close"])

    df.to_csv(csv_path)

    rows = len(df)
    last_close = round(float(df["Close"].iloc[-1]), 2)
    last_date = str(df.index[-1].date())
    warnings = []
    if rows < 200:
        warnings.append(f"only {rows} rows of history; SMA200 and 12m-return signals will be unavailable")

    write_json(meta_path, ticker, {
        "symbol": symbol,
        "rows": rows,
        "last_date": last_date,
        "last_close": last_close,
    }, warnings)

    print(f"{ticker}: fetched {rows} daily bars through {last_date}, last close {last_close}")
    for w in warnings:
        print(f"WARNING: {w}")
    return 3 if rows < 200 else 0


if __name__ == "__main__":
    sys.exit(main())

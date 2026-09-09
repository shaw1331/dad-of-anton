from __future__ import annotations

import re

from app.stock_cache.cache import get_stocks
from app.stock_cache.dto import StockEntry


def search_stocks(query: str, limit: int = 10) -> list[StockEntry]:
    stocks = get_stocks()

    if not query:
        return stocks[:limit]

    pattern = re.compile(re.escape(query), re.IGNORECASE)

    scored: list[tuple[int, StockEntry]] = []
    for stock in stocks:
        sym_match = pattern.search(stock["symbol"])
        name_match = pattern.search(stock["name"])

        pos = 999
        if sym_match:
            pos = min(pos, sym_match.start())
        if name_match:
            pos = min(pos, name_match.start())

        if pos < 999:
            scored.append((pos, stock))

    scored.sort(key=lambda x: x[0])
    return [s for _, s in scored[:limit]]

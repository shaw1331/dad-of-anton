from __future__ import annotations

import csv
import logging
from pathlib import Path

from app.stock_cache.dto import StockEntry

logger = logging.getLogger(__name__)

_stocks: list[StockEntry] = []


def get_stocks() -> list[StockEntry]:
    return _stocks


def _load() -> None:
    global _stocks
    csv_path = Path(__file__).resolve().parent.parent.parent / "STOCKS.csv"
    if not csv_path.exists():
        logger.warning("STOCKS.csv not found at %s — stock cache empty", csv_path)
        return

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _stocks = [
            {"symbol": row["SYMBOL"].strip(), "name": row["NAME OF COMPANY"].strip()}
            for row in reader
        ]
    logger.info("Loaded %d stocks into cache", len(_stocks))


_load()

"""Shared setup for stock-analyst scripts: paths, screener_scraper imports, cache, JSON IO."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/ -> stock-analyst/ -> skills/ -> .claude/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
SCRAPER_DIR = REPO_ROOT / "screener_scraper"
ANALYSIS_DIR = REPO_ROOT / "analysis-out"
REPORTS_DIR = REPO_ROOT / "reports"

sys.path.insert(0, str(SCRAPER_DIR))


def out_dir(ticker: str) -> Path:
    d = ANALYSIS_DIR / ticker.upper()
    d.mkdir(parents=True, exist_ok=True)
    return d


def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_json(path: Path, ticker: str, data: dict, warnings: list[str] | None = None) -> None:
    envelope = {
        "ticker": ticker.upper(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "warnings": warnings or [],
        **data,
    }
    path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def is_fresh(path: Path) -> bool:
    """True if the JSON file exists and was fetched today (UTC)."""
    data = read_json(path)
    if not data:
        return False
    fetched = data.get("fetched_at", "")
    return fetched[:10] == today_utc()


def parse_numeric(value) -> float | None:
    """Parse screener-style values: '1,234.5', '12.3 %', '₹ 456 Cr.', '-' -> float or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = (
        str(value)
        .replace(",", "")
        .replace("%", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Cr.", "")
        .strip()
    )
    if cleaned in ("", "-", "N/A", "--"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None

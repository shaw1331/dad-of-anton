"""History/trend extractors for screener.in company pages.

Complements screener_scraper/scrape_companies.py (which extracts latest-value ratios):
these parse the full history tables (quarters, annual P&L, shareholding trend),
the compounded-growth ranges tables, and the AJAX-loaded peers comparison.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

import _bootstrap  # noqa: F401  (sys.path setup for screener_scraper imports)
from utils import get_page
from config import BASE_URL


def parse_data_table(table) -> dict:
    """Parse a screener data-table into {"periods": [...], "rows": {name: [values...]}}."""
    periods = [th.get_text(strip=True) for th in table.select("thead th")][1:]
    rows: dict[str, list[str]] = {}
    for tr in table.select("tbody tr"):
        cells = tr.select("td")
        if not cells:
            continue
        name = cells[0].get_text(strip=True).rstrip("+").strip()
        if not name:
            continue
        rows[name] = [td.get_text(strip=True) for td in cells[1:]]
    return {"periods": periods, "rows": rows}


def _section_table(soup: BeautifulSoup, section_id: str):
    return soup.select_one(f"#{section_id} table.data-table")


def extract_quarters_history(soup: BeautifulSoup) -> dict | None:
    table = _section_table(soup, "quarters")
    return parse_data_table(table) if table else None


def extract_annual_pl(soup: BeautifulSoup) -> dict | None:
    table = _section_table(soup, "profit-loss")
    return parse_data_table(table) if table else None


def extract_shareholding_trend(soup: BeautifulSoup) -> dict | None:
    table = _section_table(soup, "shareholding")  # first data-table = quarterly view
    return parse_data_table(table) if table else None


_RANGE_LABEL = r"(10 Years|5 Years|3 Years|1 Year|TTM|Last Year)"


def extract_ranges(soup: BeautifulSoup) -> dict:
    """Parse all ranges-tables: {"Compounded Sales Growth": {"3 Years": "6%", ...}, ...}."""
    out: dict[str, dict[str, str]] = {}
    for table in soup.select("table.ranges-table"):
        text = table.get_text(" ", strip=True)
        pairs = re.findall(_RANGE_LABEL + r":\s*(-?[\d.]+%)", text)
        if not pairs:
            continue
        title = re.split(_RANGE_LABEL, text)[0].strip() or "Unknown"
        out[title] = dict(pairs)
    return out


def extract_peers(soup: BeautifulSoup) -> tuple[dict | None, str | None]:
    """Peers table; loaded via AJAX so fall back to the peers API. Returns (data, warning)."""
    table = soup.select_one("#peers table")
    if table is None:
        m = re.search(r'data-warehouse-id="(\d+)"', str(soup))
        if not m:
            return None, "peers table absent and no warehouse id found"
        peers_soup = get_page(f"{BASE_URL}/api/company/{m.group(1)}/peers/")
        table = peers_soup.select_one("table") if peers_soup else None
        if table is None:
            return None, "peers API fetch failed"
    headers = [th.get_text(strip=True) for th in table.select("tr th")]
    rows = []
    for tr in table.select("tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        if cells and any(cells):
            rows.append(cells)
    return {"headers": headers, "rows": rows}, None

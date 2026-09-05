from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup, Tag

from app.scraper.models import StockDTO

logger = logging.getLogger(__name__)


def _parse_value(text: str) -> float | None:
    """Parse a numeric value from text, handling %, commas, and N/A."""
    if not text:
        return None
    cleaned = text.strip().replace(",", "").replace("%", "")
    if not cleaned or cleaned == "-" or cleaned.upper() == "N/A":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_ema_sma(soup: BeautifulSoup) -> tuple[dict[str, float | None], dict[str, float | None]]:
    """Parse EMA and SMA values by finding the EMA & SMA h3 then its tables.

    Trendlyne structure:
        h3: "HDFC Bank EMA & SMA"
        div.card:
            div (EMA subsection):
                table (5,10,12,20 Day)  -> EMA part 1
                table (26,50,100 Day)   -> EMA part 2
            div (SMA subsection):
                table (5,10,20,30 Day)  -> SMA part 1
                table (50,100,150,200 Day) -> SMA part 2
    """
    ema: dict[str, float | None] = {}
    sma: dict[str, float | None] = {}

    # Find the h3 containing "EMA & SMA"
    h3 = None
    for tag in soup.find_all("h3"):
        if "EMA" in tag.get_text() and "SMA" in tag.get_text():
            h3 = tag
            break

    if not h3:
        return ema, sma

    # The card div is the next sibling of h3
    card = h3.find_next_sibling("div")
    if not card:
        return ema, sma

    # Get all tables inside the card
    tables = card.find_all("table")
    if len(tables) < 4:
        return ema, sma

    # EMA: tables 0 and 1
    for table in tables[0:2]:
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = _parse_value(cells[1].get_text(strip=True))
                for p in [5, 10, 12, 20, 26, 50, 100, 200]:
                    if label == f"{p} day" or label == f"{p}day":
                        ema[f"ema_{p}"] = value
                        break

    # SMA: tables 2 and 3
    for table in tables[2:4]:
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = _parse_value(cells[1].get_text(strip=True))
                for p in [5, 10, 20, 30, 50, 100, 150, 200]:
                    if label == f"{p} day" or label == f"{p}day":
                        sma[f"sma_{p}"] = value
                        break

    return ema, sma


def _parse_momentum(soup: BeautifulSoup) -> dict[str, float | None]:
    """Parse momentum indicators from table rows."""
    result: dict[str, float | None] = {}
    mapping = {
        "day rsi": "rsi",
        "day macd signal line": "macd_signal",
        "day macd": "macd",
        "day adx": "adx",
        "day atr": "atr",
        "day mfi": "mfi",
        "day commodity channel index": "cci",
        "day roc125": "roc_125",
        "day roc21": "roc_21",
        "william": "williams_r",
    }

    # Sort by length descending so "day macd signal line" matches before "day macd"
    sorted_mapping = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)

    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value_text = cells[1].get_text(strip=True)
            for pattern, key in sorted_mapping:
                if pattern in label:
                    result[key] = _parse_value(value_text)
                    break

    return result


def _parse_support_resistance(soup: BeautifulSoup) -> dict[str, float | None]:
    """Parse support/resistance levels from table rows and standalone elements."""
    result: dict[str, float | None] = {}
    sr_mapping = {
        "first resistance": "r1",
        "second resistance": "r2",
        "third resistance": "r3",
        "first support": "s1",
        "second support": "s2",
        "third support": "s3",
    }

    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value_text = cells[1].get_text(strip=True)
            for pattern, key in sr_mapping.items():
                if pattern in label:
                    result[key] = _parse_value(value_text)
                    break

    # Pivot: appears as standalone text "PIVOT" with value in a sibling div
    # Structure: <div>712.32</div><div class="news-sm-head">PIVOT</div>
    if not result.get("pivot"):
        for el in soup.find_all(string=re.compile(r"^PIVOT$", re.I)):
            parent = el.parent
            if parent:
                prev = parent.find_previous_sibling(["div", "span", "td"])
                if prev:
                    result["pivot"] = _parse_value(prev.get_text(strip=True))
                    if result["pivot"] is not None:
                        break

    return result


def _parse_returns(soup: BeautifulSoup) -> dict[str, float | None]:
    """Parse price return percentages.

    Structure on Trendlyne:
        <div class="col-xs-6 ...">
            <div>
                <span>↓</span>
                <span class="value-span">-4.0%</span>
            </div>
            <div class="... price-change-param ...">Over 1 Month</div>
        </div>
    The value is in a <span> inside the grandparent of the "Over X" text node.
    """
    result: dict[str, float | None] = {}
    mapping = {
        "over 1 month": "return_1m",
        "over 3 months": "return_3m",
        "over 6 months": "return_6m",
        "over 1 year": "return_1y",
    }

    for text_node in soup.find_all(string=re.compile(r"^Over \d+ (Months?|Years?|Weeks?)$", re.I)):
        label_text = text_node.strip().lower()
        for pattern, key in mapping.items():
            if pattern in label_text:
                parent = text_node.parent  # div containing "Over X Month"
                grandparent = parent.parent if parent else None
                if grandparent:
                    # Find span containing a percentage value
                    span = grandparent.find("span", string=re.compile(r"-?\d+\.?\d*%"))
                    if span:
                        result[key] = _parse_value(span.get_text(strip=True))
                break

    return result


def _parse_beta(soup: BeautifulSoup) -> dict[str, float | None]:
    """Parse beta values from the beta section table."""
    result: dict[str, float | None] = {}
    mapping = {
        "1 month": "beta_1m",
        "3 month": "beta_3m",
        "3 months": "beta_3m",
        "1 year": "beta_1y",
        "3 year": "beta_3y",
        "3 years": "beta_3y",
    }

    # Find the h3 containing "Beta"
    beta_h3 = None
    for tag in soup.find_all("h3"):
        text = tag.get_text(strip=True)
        if "Beta" in text and "Delivery" not in text:
            beta_h3 = tag
            break

    if not beta_h3:
        return result

    # Get the card div after the h3
    card = beta_h3.find_next_sibling("div")
    if not card:
        return result

    # Parse table rows
    for row in card.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value_text = cells[1].get_text(strip=True)
            for pattern, key in mapping.items():
                if pattern in label:
                    result[key] = _parse_value(value_text)
                    break

    return result


def map_search_result(json_data: list | dict) -> str | None:
    """Extract stock_id from Trendlyne search API response."""
    if isinstance(json_data, dict):
        items = [json_data]
    elif isinstance(json_data, list):
        items = json_data
    else:
        return None

    for item in items:
        stock_id = item.get("k")
        if stock_id:
            return str(stock_id)

    return None


def map_index_search_result(json_data: list | dict) -> dict | None:
    """Extract index info from Trendlyne search API response."""
    if isinstance(json_data, dict):
        items = [json_data]
    elif isinstance(json_data, list):
        items = json_data
    else:
        return None

    for item in items:
        if item.get("category") == "Index":
            return {
                "stock_id": str(item.get("k", "")),
                "ticker": item.get("id", ""),
                "slug": item.get("slugname", ""),
                "name": item.get("label", "").split("(")[0].strip(),
            }

    return None


def map_technicals(html: str, ticker: str, url: str) -> StockDTO:
    """Parse Trendlyne technical analysis HTML and build a StockDTO."""
    soup = BeautifulSoup(html, "html.parser")

    # Parse all sections
    ema_data, sma_data = _parse_ema_sma(soup)
    momentum_data = _parse_momentum(soup)
    sr_data = _parse_support_resistance(soup)
    returns_data = _parse_returns(soup)
    beta_data = _parse_beta(soup)

    # Merge all data
    all_data: dict[str, float | None] = {}
    all_data.update(ema_data)
    all_data.update(sma_data)
    all_data.update(momentum_data)
    all_data.update(sr_data)
    all_data.update(returns_data)
    all_data.update(beta_data)

    # Filter out None values
    data = {k: v for k, v in all_data.items() if v is not None}

    # Get stock name from page title
    name = ticker
    title = soup.find("title")
    if title:
        title_text = title.get_text(strip=True)
        name_match = re.match(r"^(.+?)(?:\s+Share Price|\s+Technical)", title_text)
        if name_match:
            name = name_match.group(1).strip()

    # Get company name from h1
    company_name = name
    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(strip=True)
        if "Technical Analysis" in h1_text:
            company_name = h1_text.split("Technical Analysis")[0].strip()

    return StockDTO(
        ticker=ticker,
        name=name,
        company_name=company_name,
        source="trendlyne",
        data=data,
        url=url,
    )

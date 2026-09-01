from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup, NavigableString, Tag

from pydantic import BaseModel, Field

from app.scraper.models import StockDTO


class ScreenerStockData(BaseModel):
    ratios: dict[str, dict[str, str]] = Field(default_factory=dict)
    quarterly_results: dict[str, dict[str, str]] = Field(default_factory=dict)
    profit_loss: dict[str, dict[str, str]] = Field(default_factory=dict)
    balance_sheet: dict[str, dict[str, str]] = Field(default_factory=dict)
    cash_flow: dict[str, dict[str, str]] = Field(default_factory=dict)
    shareholding: dict[str, str] = Field(default_factory=dict)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


def _extract_unit(value_span: Tag) -> str:
    """Extract the unit text from a .value span, excluding the .number child.

    Looks at direct text children and any non-.number child elements
    to find currency symbols (₹) and unit suffixes (Cr., %, etc.).
    """
    parts: list[str] = []

    for child in value_span.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                parts.append(text)
        elif isinstance(child, Tag):
            if "number" not in child.get("class", []):
                text = child.get_text(strip=True)
                if text:
                    parts.append(text)

    return " ".join(parts).strip()


def map_ratios(soup: BeautifulSoup) -> dict[str, dict[str, str]]:
    """Extract ratios with units from #top-ratios section.

    Returns a dict mapping ratio name to {"value": "...", "unit": "..."}.
    Example: {"Market Cap": {"value": "34,386", "unit": "₹ Cr."}}
    """
    ratios: dict[str, dict[str, str]] = {}
    ratios_list = soup.select_one("#top-ratios")
    if not ratios_list:
        return ratios

    for li in ratios_list.select("li"):
        name_span = li.select_one(".name")
        value_span = li.select_one(".value")
        if name_span and value_span:
            name = name_span.get_text(strip=True)
            number = value_span.select_one(".number")
            value = number.get_text(strip=True) if number else value_span.get_text(strip=True)
            unit = _extract_unit(value_span)
            ratios[name] = {"value": value, "unit": unit}

    return ratios


def _parse_data_table(soup: BeautifulSoup, section_id: str) -> dict[str, dict[str, str]]:
    """Parse a financial data table (quarters, P&L, balance sheet, cash flow).

    Returns a dict mapping date strings (from data-date-key) to row dicts.
    Each row dict maps the row label to its value.

    Also includes a special "units" key with the table's unit subtitle.
    """
    result: dict[str, dict[str, str]] = {}
    section = soup.select_one(f"#{section_id}")
    if not section:
        return result

    table = section.select_one("table")
    if not table:
        return result

    thead = table.select_one("thead")
    if not thead:
        return result

    header_row = thead.select_one("tr")
    if not header_row:
        return result

    th_elements = header_row.select("th")
    if not th_elements:
        return result

    columns: list[str] = []
    for th in th_elements[1:]:
        date_key = th.get("data-date-key", "")
        display = th.get_text(strip=True)
        columns.append(date_key if date_key else display)

    tbody = table.select_one("tbody")
    if not tbody:
        return result

    for row in tbody.select("tr"):
        cells = row.select("td")
        if not cells:
            continue

        label = cells[0].get_text(strip=True)
        if not label:
            continue

        value_cells = cells[1:]
        for i, cell in enumerate(value_cells):
            if i < len(columns):
                text = cell.get_text(strip=True)
                date_key = columns[i]
                if date_key not in result:
                    result[date_key] = {}
                result[date_key][label] = text

    return result


def map_shareholding(soup: BeautifulSoup) -> dict[str, str]:
    """Extract shareholding percentages from #shareholding table."""
    shareholding: dict[str, str] = {}
    shareholding_table = soup.select_one("#shareholding table")
    if not shareholding_table:
        return shareholding

    rows = shareholding_table.select("tr")
    for row in rows:
        cells = row.select("td")
        if not cells or len(cells) < 2:
            continue
        category = cells[0].get_text(strip=True)
        value = cells[-1].get_text(strip=True)
        shareholding[category] = value

    return shareholding


def map_pros_cons(soup: BeautifulSoup) -> tuple[list[str], list[str]]:
    """Extract pros and cons from #analysis section."""
    pros: list[str] = []
    cons: list[str] = []

    pros_section = soup.select_one(".pros ul")
    if pros_section:
        for li in pros_section.select("li"):
            text = li.get_text(strip=True)
            if text:
                pros.append(text)

    cons_section = soup.select_one(".cons ul")
    if cons_section:
        for li in cons_section.select("li"):
            text = li.get_text(strip=True)
            if text:
                cons.append(text)

    return pros, cons


def map_company_page(soup: BeautifulSoup, ticker: str, url: str) -> StockDTO:
    """Map a company page to a StockDTO."""
    ratios = map_ratios(soup)
    quarterly_results = _parse_data_table(soup, "quarters")
    profit_loss = _parse_data_table(soup, "profit-loss")
    balance_sheet = _parse_data_table(soup, "balance-sheet")
    cash_flow = _parse_data_table(soup, "cash-flow")
    shareholding = map_shareholding(soup)
    pros, cons = map_pros_cons(soup)

    company_name = ""
    title = soup.select_one("h1")
    if title:
        company_name = title.get_text(strip=True)

    sector: str | None = None
    industry: str | None = None
    sector_links = soup.select("#peers a[href*='/market/']")
    if sector_links:
        sector = sector_links[0].get_text(strip=True) if len(sector_links) > 0 else None
        industry = sector_links[-1].get_text(strip=True) if len(sector_links) > 1 else None

    screener_data = ScreenerStockData(
        ratios=ratios,
        quarterly_results=quarterly_results,
        profit_loss=profit_loss,
        balance_sheet=balance_sheet,
        cash_flow=cash_flow,
        shareholding=shareholding,
        pros=pros,
        cons=cons,
    )

    return StockDTO(
        ticker=ticker,
        name=company_name,
        company_name=company_name,
        sector=sector,
        industry=industry,
        source="screener",
        data=screener_data.model_dump(),
        url=url,
        scraped_at=datetime.now(timezone.utc),
    )

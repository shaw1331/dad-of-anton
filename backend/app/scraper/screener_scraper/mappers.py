from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup

from app.scraper.models import StockDTO
from app.scraper.screener_scraper.config import COMPANY_DATA_POINTS


def map_ratios(soup: BeautifulSoup) -> dict[str, str]:
    """Extract ratios from #top-ratios section."""
    ratios: dict[str, str] = {}
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
            ratios[name] = value

    return ratios


def map_quarterly(soup: BeautifulSoup) -> dict[str, str]:
    """Extract latest quarter values from #quarters table."""
    quarterly: dict[str, str] = {}
    quarters_table = soup.select_one("#quarters table")
    if not quarters_table:
        return quarterly

    rows = quarters_table.select("tr")
    for row in rows:
        cells = row.select("td")
        if not cells:
            continue
        label = cells[0].get_text(strip=True)
        for cell in reversed(cells[1:]):
            text = cell.get_text(strip=True)
            if text:
                quarterly[label] = text
                break

    return quarterly


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
    quarterly = map_quarterly(soup)
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

    return StockDTO(
        ticker=ticker,
        name=company_name,
        company_name=company_name,
        sector=sector,
        industry=industry,
        ratios=ratios,
        quarterly=quarterly,
        shareholding=shareholding,
        pros=pros,
        cons=cons,
        url=url,
        scraped_at=datetime.now(timezone.utc),
    )

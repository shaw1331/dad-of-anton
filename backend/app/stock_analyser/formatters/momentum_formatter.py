from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.stock_analyser.formatters import StockDataFormatorFactory
from app.stock_analyser.formatters.base import BaseStockFormatter

_PROMPT_DIR = Path(__file__).parent


def _ratio(stock_data: dict, name: str) -> str:
    """Extract a value from data['ratios']."""
    entry = stock_data.get("data", {}).get("ratios", {}).get(name, {})
    return entry.get("value", "N/A") if isinstance(entry, dict) else "N/A"


def _quarterly(stock_data: dict, period: str, field: str) -> str:
    """Extract a value from the latest quarterly results."""
    quarterly = stock_data.get("data", {}).get("quarterly_results", {})
    if not quarterly:
        return "N/A"
    latest = quarterly.get(period, {})
    if not latest:
        keys = sorted(quarterly.keys(), reverse=True)
        latest = quarterly[keys[0]] if keys else {}
    return latest.get(field, "N/A")


def _format_news(idx: int, article: dict) -> str:
    """Format a single analyzed news article as Markdown."""
    news_id = article.get("news_id", f"NEWS_{idx:03d}")
    source = article.get("source", "Unknown")
    pub_date = article.get("pub_date", "Unknown")
    sentiment = article.get("trader_sentiment", "neutral").upper()
    impact = article.get("impact", "low").upper()
    summary = article.get("detailed_summary") or article.get("raw_summary") or "No summary available."
    reasoning = article.get("impact_reasoning", "No reasoning available.")

    return (
        f"## News {idx}\n\n"
        f"- News ID: {news_id}\n"
        f"- Source: {source}\n"
        f"- Published: {pub_date}\n"
        f"- Sentiment: {sentiment}\n"
        f"- Impact: {impact}\n\n"
        f"### Summary\n\n{summary}\n\n"
        f"### Impact Reasoning\n\n{reasoning}\n\n"
        f"---"
    )


class MomentumFormatter(BaseStockFormatter):
    """Formats stock data and news into a momentum analysis Markdown prompt."""

    def format(self, stock_data: dict, analyzed_news: list[dict], meta: dict) -> str:
        ticker = meta.get("ticker", stock_data.get("ticker", "N/A"))
        company = meta.get("company_name") or stock_data.get("company_name") or stock_data.get("name", "N/A")
        sector = meta.get("sector") or stock_data.get("sector") or "N/A"
        industry = meta.get("industry") or stock_data.get("industry") or "N/A"
        data_as_of = datetime.now().strftime("%Y-%m-%d")

        # Fundamental context — valuation & profitability
        current_price = _ratio(stock_data, "Current Price")
        market_cap = _ratio(stock_data, "Market Cap")
        pe = _ratio(stock_data, "Stock P/E")
        roe = _ratio(stock_data, "ROE")
        roce = _ratio(stock_data, "ROCE")
        book_value = _ratio(stock_data, "Book Value")
        div_yield = _ratio(stock_data, "Dividend Yield")

        # Latest financials
        quarterly = stock_data.get("data", {}).get("quarterly_results", {})
        latest_period = sorted(quarterly.keys(), reverse=True)[0] if quarterly else None
        sales = _quarterly(stock_data, latest_period or "", "Sales") if latest_period else "N/A"
        op_profit = _quarterly(stock_data, latest_period or "", "Operating Profit") if latest_period else "N/A"
        opm = _quarterly(stock_data, latest_period or "", "OPM %") if latest_period else "N/A"
        net_profit = _quarterly(stock_data, latest_period or "", "Net Profit") if latest_period else "N/A"
        eps = _quarterly(stock_data, latest_period or "", "EPS in Rs") if latest_period else "N/A"

        # Balance sheet items
        balance = stock_data.get("data", {}).get("balance_sheet", {})
        latest_bs = balance.get(latest_period, {}) if latest_period else {}
        borrowings = latest_bs.get("Borrowings", "N/A")

        # News section
        news_section = ""
        if analyzed_news:
            for i, article in enumerate(analyzed_news, 1):
                news_section += _format_news(i, article) + "\n\n"
        else:
            news_section = (
                "No analyzed news articles available for this stock.\n"
            )

        template = (_PROMPT_DIR / "momentum_prompt.md").read_text()

        return template.format(
            company=company,
            ticker=ticker,
            sector=sector,
            industry=industry,
            data_as_of=data_as_of,
            current_price=current_price,
            market_cap=market_cap,
            pe=pe,
            roe=roe,
            roce=roce,
            book_value=book_value,
            div_yield=div_yield,
            sales=sales,
            op_profit=op_profit,
            opm=opm,
            net_profit=net_profit,
            eps=eps,
            borrowings=borrowings,
            news_section=news_section,
        )


from app.stock_analyser.analysis.prompts.momentum import MomentumStrategy

StockDataFormatorFactory.register(MomentumStrategy, MomentumFormatter)

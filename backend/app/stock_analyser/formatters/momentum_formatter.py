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


def _tl(trendlyne_data: dict, key: str) -> str:
    """Extract a value from Trendlyne technical data."""
    val = trendlyne_data.get("data", {}).get(key)
    if val is None:
        return "N/A"
    return f"{val}"


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val:+.2f}%"


def _fmt_num(val: float | None, decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def _compute_ma_alignment(price: float | None, ema20: float | None, ema50: float | None, ema200: float | None) -> str:
    if price is None or ema20 is None or ema50 is None or ema200 is None:
        return "N/A"
    if price > ema20 > ema50 > ema200:
        return "BULLISH"
    if price < ema20 < ema50 < ema200:
        return "BEARISH"
    return "MIXED"


def _price_vs_ema(price: float | None, ema: float | None) -> str:
    if price is None or ema is None:
        return "N/A"
    return "ABOVE" if price > ema else "BELOW"


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

        # --- Fundamental context (from Screener) ---
        current_price = _ratio(stock_data, "Current Price")
        market_cap = _ratio(stock_data, "Market Cap")
        pe = _ratio(stock_data, "Stock P/E")
        roe = _ratio(stock_data, "ROE")
        roce = _ratio(stock_data, "ROCE")
        book_value = _ratio(stock_data, "Book Value")
        div_yield = _ratio(stock_data, "Dividend Yield")

        # Latest financials
        quarterly = stock_data.get("data", {}).get("quarterly_results", {})
        latest_period = sorted(quarterly.keys(), reverse=True)[0] if quarterly else "N/A"
        sales = _quarterly(stock_data, latest_period, "Sales") if latest_period != "N/A" else "N/A"
        op_profit = _quarterly(stock_data, latest_period, "Operating Profit") if latest_period != "N/A" else "N/A"
        opm = _quarterly(stock_data, latest_period, "OPM %") if latest_period != "N/A" else "N/A"
        net_profit = _quarterly(stock_data, latest_period, "Net Profit") if latest_period != "N/A" else "N/A"
        eps = _quarterly(stock_data, latest_period, "EPS in Rs") if latest_period != "N/A" else "N/A"

        # Balance sheet items
        balance = stock_data.get("data", {}).get("balance_sheet", {})
        latest_bs = balance.get(latest_period, {}) if latest_period != "N/A" else {}
        borrowings = latest_bs.get("Borrowings", "N/A")

        # --- Technical data (from Trendlyne) ---
        tl = stock_data.get("trendlyne") or {}
        tl_data = tl.get("data", {})

        # Parse numeric values from Trendlyne
        price_num = tl_data.get("ema_20")  # use as proxy for current price if available
        ema_20 = tl_data.get("ema_20")
        ema_50 = tl_data.get("ema_50")
        ema_200 = tl_data.get("ema_200")
        sma_20 = tl_data.get("sma_20")
        sma_50 = tl_data.get("sma_50")
        sma_200 = tl_data.get("sma_200")
        rsi = tl_data.get("rsi")
        macd = tl_data.get("macd")
        macd_signal = tl_data.get("macd_signal")
        adx = tl_data.get("adx")
        atr = tl_data.get("atr")
        mfi = tl_data.get("mfi")
        cci = tl_data.get("cci")
        roc_21 = tl_data.get("roc_21")
        williams_r = tl_data.get("williams_r")
        r1 = tl_data.get("r1")
        r2 = tl_data.get("r2")
        r3 = tl_data.get("r3")
        s1 = tl_data.get("s1")
        s2 = tl_data.get("s2")
        s3 = tl_data.get("s3")
        pivot = tl_data.get("pivot")
        return_1m = tl_data.get("return_1m")
        return_3m = tl_data.get("return_3m")
        return_6m = tl_data.get("return_6m")
        return_1y = tl_data.get("return_1y")

        # Try to get current price from Trendlyne returns or Screener
        try:
            price_num = float(current_price.replace(",", "")) if current_price != "N/A" else None
        except (ValueError, AttributeError):
            price_num = None

        # Derived values
        macd_histogram = None
        if macd is not None and macd_signal is not None:
            macd_histogram = macd - macd_signal

        ma_alignment = _compute_ma_alignment(price_num, ema_20, ema_50, ema_200)
        price_vs_ema20 = _price_vs_ema(price_num, ema_20)
        price_vs_ema50 = _price_vs_ema(price_num, ema_50)
        price_vs_ema200 = _price_vs_ema(price_num, ema_200)

        # Distance from support / resistance
        distance_from_resistance = "N/A"
        distance_from_support = "N/A"
        if price_num and r1:
            distance_from_resistance = f"{((r1 - price_num) / price_num) * 100:.2f}%"
        if price_num and s1:
            distance_from_support = f"{((price_num - s1) / price_num) * 100:.2f}%"

        # Relative strength — not available from Trendlyne
        rs_benchmark = "N/A"
        rs_stock_return = "N/A"
        rs_benchmark_return = "N/A"
        rs_performance = "N/A"

        # News section
        news_section = ""
        if analyzed_news:
            for i, article in enumerate(analyzed_news, 1):
                news_section += _format_news(i, article) + "\n\n"
        else:
            news_section = "No analyzed news articles available for this stock.\n"

        template = (_PROMPT_DIR / "momentum_prompt.md").read_text()

        return template.format(
            company=company,
            ticker=ticker,
            sector=sector,
            industry=industry,
            data_as_of=data_as_of,
            # Technical — Price
            current_price=current_price,
            return_1m=_fmt_pct(return_1m),
            return_3m=_fmt_pct(return_3m),
            return_6m=_fmt_pct(return_6m),
            return_1y=_fmt_pct(return_1y),
            # Technical — Moving Averages
            ema_20=_fmt_num(ema_20),
            ema_50=_fmt_num(ema_50),
            ema_200=_fmt_num(ema_200),
            sma_20=_fmt_num(sma_20),
            sma_50=_fmt_num(sma_50),
            sma_200=_fmt_num(sma_200),
            price_vs_ema20=price_vs_ema20,
            price_vs_ema50=price_vs_ema50,
            price_vs_ema200=price_vs_ema200,
            ma_alignment=ma_alignment,
            # Technical — Momentum Indicators
            rsi=_fmt_num(rsi, 1),
            macd=_fmt_num(macd),
            macd_signal=_fmt_num(macd_signal),
            macd_histogram=_fmt_num(macd_histogram),
            adx=_fmt_num(adx, 1),
            mfi=_fmt_num(mfi, 1),
            cci=_fmt_num(cci, 1),
            roc_21=_fmt_pct(roc_21),
            williams_r=_fmt_num(williams_r, 1),
            # Technical — Relative Strength
            rs_benchmark=rs_benchmark,
            rs_stock_return=rs_stock_return,
            rs_benchmark_return=rs_benchmark_return,
            rs_performance=rs_performance,
            # Technical — Support / Resistance
            r1=_fmt_num(r1),
            r2=_fmt_num(r2),
            r3=_fmt_num(r3),
            s1=_fmt_num(s1),
            s2=_fmt_num(s2),
            s3=_fmt_num(s3),
            pivot=_fmt_num(pivot),
            distance_from_resistance=distance_from_resistance,
            distance_from_support=distance_from_support,
            # Technical — Volatility
            atr=_fmt_num(atr),
            # Fundamental
            market_cap=market_cap,
            pe=pe,
            roe=roe,
            roce=roce,
            book_value=book_value,
            div_yield=div_yield,
            latest_period=latest_period,
            sales=sales,
            op_profit=op_profit,
            opm=opm,
            net_profit=net_profit,
            eps=eps,
            borrowings=borrowings,
            # News
            news_section=news_section,
        )


from app.stock_analyser.analysis.prompts.momentum import MomentumStrategy

StockDataFormatorFactory.register(MomentumStrategy, MomentumFormatter)

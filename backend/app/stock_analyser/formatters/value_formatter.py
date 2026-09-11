from __future__ import annotations

from app.stock_analyser.formatters import StockDataFormatorFactory
from app.stock_analyser.formatters.base import BaseStockFormatter


class ValueInvestingFormatter(BaseStockFormatter):
    """Formats stock data for value investing analysis (placeholder)."""

    def format(self, stock_data: dict, analyzed_news: list[dict], meta: dict) -> str:
        lines = [
            "# VALUE INVESTING ANALYSIS",
            "",
            "Analyze this stock for value investing potential.",
            "",
            "## Stock Info",
            f"- Ticker: {stock_data.get('ticker', 'N/A')}",
            f"- Company: {stock_data.get('company_name') or stock_data.get('name', 'N/A')}",
            f"- Sector: {stock_data.get('sector') or 'N/A'}",
            f"- Industry: {stock_data.get('industry') or 'N/A'}",
            "",
            "## Financial Ratios",
        ]

        data = stock_data.get("data", {})
        ratios = data.get("ratios", {})
        for key, entry in ratios.items():
            val = entry.get("value", "N/A") if isinstance(entry, dict) else entry
            lines.append(f"- {key}: {val}")

        lines.append("")
        lines.append("## Latest Financials")
        quarterly = data.get("quarterly_results", {})
        if quarterly:
            latest_key = sorted(quarterly.keys(), reverse=True)[0]
            for field, val in quarterly[latest_key].items():
                if field != "Units":
                    lines.append(f"- {field}: {val}")

        lines.append("")
        lines.append("## Pros")
        for p in data.get("pros", []):
            lines.append(f"- {p}")

        lines.append("")
        lines.append("## Cons")
        for c in data.get("cons", []):
            lines.append(f"- {c}")

        if analyzed_news:
            lines.append("")
            lines.append("## Recent News")
            for i, article in enumerate(analyzed_news, 1):
                sentiment = article.get("trader_sentiment", "neutral")
                summary = article.get("detailed_summary") or article.get("raw_summary", "")
                lines.append(f"- [{sentiment.upper()}] {summary}")

        lines.append("")
        lines.append("## PRE-COMPUTED TECHNICAL LEVELS")
        lines.append("")
        levels = stock_data.get("levels")
        if levels and levels.get("recommendation"):
            l = levels
            lr = l.get("level_reasoning", "")
            entry = str(l.get("entry_above", "N/A"))
            slv = str(l.get("stop_loss", "N/A"))
            targets = ", ".join([str(t) for t in l.get("targets", [])]) if l.get("targets") else "N/A"
            rec = l.get("recommendation", "N/A")
            conv = l.get("conviction", "N/A")
            lines.append(f"- Recommendation: {rec}")
            lines.append(f"- Conviction: {conv}")
            lines.append(f"- Entry Above: {entry}")
            lines.append(f"- Stop-Loss: {slv}")
            lines.append(f"- Targets: {targets}")
            lines.append(f"- Level Reasoning: {lr}")
            vm = l.get("volume_metrics")
            if vm:
                lines.append("")
                lines.append("### Volume Metrics")
                lines.append(f"- 10D Avg Volume: {vm['avg_volume_10d']:.0f}")
                lines.append(f"- 20D Avg Volume: {vm['avg_volume_20d']:.0f}")
                lines.append(f"- Current Volume: {vm['current_volume']:.0f}")
                lines.append(f"- Volume Spike: {'YES' if vm['volume_spike'] else 'NO'}")
                lines.append(f"- Volume Trend: {vm['volume_trend']}")
        else:
            lines.append("No levels data available (insufficient technical data).")
        lines.append("")
        lines.append("These levels were derived from EMA alignment, support/resistance, RSI, ADX, ATR, and volume data. Validate or challenge them in your analysis.")

        return "\n".join(lines)


from app.stock_analyser.analysis.prompts.value_investing import ValueInvestingStrategy

StockDataFormatorFactory.register(ValueInvestingStrategy, ValueInvestingFormatter)

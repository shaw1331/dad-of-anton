from __future__ import annotations

from pathlib import Path

from app.stock_analyser.analysis.interfaces import AnalysisStrategy
from app.stock_analyser.analysis.prompts.base import format_stock_summary

_PROMPT_DIR = Path(__file__).parent


class MomentumStrategy(AnalysisStrategy):
    """Momentum trading analysis strategy for trend-following."""

    name = "momentum"

    def get_system_prompt(self) -> str:
        return (_PROMPT_DIR / "momentum.md").read_text()

    def get_analysis_prompt(self, stock_data: dict) -> str:
        summary = format_stock_summary(stock_data)
        analysis_prompt = f"""
            Analyze the following stock using the momentum trading framework defined in the system instructions.

            STOCK DATA:
            {summary}

            Important:
            - Use only the supplied data.
            - Do not invent missing technical indicators.
            - Give greater weight to recent momentum evidence.
            - Fundamentals are secondary context and must not override technical momentum.
            - If critical momentum data is missing, prefer HOLD and reduce confidence.
            - Explicitly identify missing data.
            - Return ONLY the required JSON object.
            """
        return analysis_prompt
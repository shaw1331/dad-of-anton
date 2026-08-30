from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.stock_analyser.analysis.interfaces import AnalysisStrategy
from app.stock_analyser.analysis.prompts.base import format_stock_summary

_PROMPT_DIR = Path(__file__).parent


class KeyFactor(BaseModel):
    factor: str
    impact: Literal["BULLISH", "NEUTRAL", "BEARISH"]
    evidence: str


class MomentumAnalysis(BaseModel):
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0.0, le=1.0)
    momentum_score: float = Field(ge=-1.0, le=1.0)
    timeframe: Literal["short_term", "medium_term", "long_term"]
    data_quality: Literal["HIGH", "MEDIUM", "LOW"]
    reasoning: str
    key_factors: list[KeyFactor]
    risks: list[str]
    missing_data: list[str]


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
            """
        return analysis_prompt

    def get_output_model(self) -> type[MomentumAnalysis]:
        return MomentumAnalysis
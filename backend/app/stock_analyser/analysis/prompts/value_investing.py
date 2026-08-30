from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.stock_analyser.analysis.interfaces import AnalysisStrategy
from app.stock_analyser.analysis.prompts.base import format_stock_summary


class ValueInvestingAnalysis(BaseModel):
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    key_factors: list[str]
    risks: list[str]
    margin_of_safety: str | None = None


class ValueInvestingStrategy(AnalysisStrategy):
    """Value investing analysis strategy following Graham/Buffett principles."""

    name = "value_investing"

    def get_system_prompt(self) -> str:
        return (
            "You are a value investing analyst following the principles of "
            "Benjamin Graham and Warren Buffett.\n\n"
            "Your task is to analyze stocks based on intrinsic value, financial "
            "health, and margin of safety.\n\n"
            "Focus on:\n"
            "- Financial strength (low debt, consistent earnings)\n"
            "- Valuation metrics (P/E, P/B, EV/EBITDA relative to peers)\n"
            "- Earnings quality and consistency\n"
            "- Competitive moat and business quality\n"
            "- Margin of safety (current price vs intrinsic value)"
        )

    def get_analysis_prompt(self, stock_data: dict) -> str:
        summary = format_stock_summary(stock_data)
        return (
            f"Analyze this stock for value investing potential:\n\n"
            f"{summary}\n\n"
            "Determine recommendation, confidence, reasoning, key factors, "
            "risks, and margin of safety."
        )

    def get_output_model(self) -> type[ValueInvestingAnalysis]:
        return ValueInvestingAnalysis

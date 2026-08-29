from __future__ import annotations

from app.stock_analyser.analysis.interfaces import AnalysisStrategy
from app.stock_analyser.analysis.prompts.base import format_stock_summary


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
            "- Margin of safety (current price vs intrinsic value)\n\n"
            'Output a JSON object with:\n'
            "{\n"
            '  "recommendation": "BUY" | "HOLD" | "SELL",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "reasoning": "detailed analysis...",\n'
            '  "key_factors": ["factor1", "factor2", ...],\n'
            '  "risks": ["risk1", "risk2", ...]\n'
            "}"
        )

    def get_analysis_prompt(self, stock_data: dict) -> str:
        summary = format_stock_summary(stock_data)
        return (
            f"Analyze this stock for value investing potential:\n\n"
            f"{summary}\n\n"
            "Provide your analysis as a JSON object with the following fields:\n"
            '- recommendation: "BUY", "HOLD", or "SELL"\n'
            "- confidence: A number between 0.0 and 1.0\n"
            "- reasoning: Detailed analysis (2-3 paragraphs)\n"
            "- key_factors: List of 3-5 key factors influencing your decision\n"
            "- risks: List of 2-3 risks to consider"
        )

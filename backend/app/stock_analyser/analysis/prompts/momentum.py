from __future__ import annotations

from app.stock_analyser.analysis.interfaces import AnalysisStrategy
from app.stock_analyser.analysis.prompts.base import format_stock_summary


class MomentumStrategy(AnalysisStrategy):
    """Momentum trading analysis strategy for trend-following."""

    name = "momentum"

    def get_system_prompt(self) -> str:
        return (
            "You are a momentum trading analyst specializing in trend-following "
            "strategies.\n\n"
            "Your task is to analyze stocks based on price momentum, volume, and "
            "technical indicators.\n\n"
            "Focus on:\n"
            "- Price trend direction and strength\n"
            "- Volume patterns (increasing/decreasing)\n"
            "- Relative strength vs market/sector\n"
            "- Moving average alignment\n"
            "- Breakout/breakdown patterns\n\n"
            "IMPORTANT: Output ONLY a valid JSON object. No extra text, no explanation, "
            "no markdown, no code blocks. Just the raw JSON.\n\n"
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
            f"Analyze this stock for momentum trading potential:\n\n"
            f"{summary}\n\n"
            "Output ONLY a valid JSON object. No extra text, no explanation, "
            "no markdown, no code blocks. Just the raw JSON with these fields:\n"
            '- recommendation: "BUY", "HOLD", or "SELL"\n'
            "- confidence: A number between 0.0 and 1.0\n"
            "- reasoning: Detailed analysis (2-3 paragraphs)\n"
            "- key_factors: List of 3-5 key factors influencing your decision\n"
            "- risks: List of 2-3 risks to consider"
        )

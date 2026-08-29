"""Integration test for stock analysis pipeline using Google Gemini.

Run: cd backend && python -m tests.test_analyze_stocks_gemini

Requires: GOOGLE_API_KEY set in .env
"""
from __future__ import annotations

import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Sample stock data matching the structure from screener scraper
SAMPLE_STOCK = {
    "ticker": "HDFCBANK",
    "name": "HDFC Bank Ltd.",
    "company_name": "HDFC Bank Ltd.",
    "sector": "Finance",
    "industry": "Banks",
    "source": "screener",
    "data": {
        "ratios": {
            "Market Cap": "₹12,50,000 Cr.",
            "P/E": "19.2",
            "P/B": "2.8",
            "ROE": "16.5%",
            "ROCE": "17.8%",
            "Debt to equity": "0.0",
            "EPS": "₹83.5",
        },
        "quarterly": {
            "Sales": "₹68,000 Cr.",
            "Net Profit": "₹18,500 Cr.",
            "OPM": "42.1%",
        },
        "shareholding": {
            "Promoters": "0.0%",
            "FII": "48.2%",
            "DII": "34.5%",
            "Public": "17.3%",
        },
        "pros": [
            "Zero promoter pledge",
            "Healthy dividend payout",
            "Good quarterly growth",
        ],
        "cons": [
            "Low promoter holding",
            "High PE ratio compared to peers",
        ],
    },
    "url": "https://www.screener.in/company/HDFCBANK/",
    "scraped_at": "2025-01-01T00:00:00Z",
}


def test_gemini_analysis_pipeline() -> None:
    """Test the full analysis pipeline with Google Gemini."""
    logger.info("=== Gemini Stock Analysis Integration Test ===")

    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set. Skipping test.")
        sys.exit(1)

    # 1. Test strategy
    logger.info("Step 1: Loading strategy...")
    from app.stock_analyser.analysis import AnalysisFactory

    logger.info("Registered strategies: %s", list(AnalysisFactory._strategies.keys()))
    strategy = AnalysisFactory.get("value_investing")
    logger.info("Strategy loaded: %s", strategy.name)

    system_prompt = strategy.get_system_prompt()
    analysis_prompt = strategy.get_analysis_prompt(SAMPLE_STOCK)
    logger.info("System prompt length: %d chars", len(system_prompt))
    logger.info("Analysis prompt length: %d chars", len(analysis_prompt))

    # 2. Test agent graph with Gemini
    logger.info("Step 2: Loading agent graph (Gemini)...")
    from langchain.chat_models import init_chat_model

    llm = init_chat_model(
        model="gemini-2.0-flash",
        model_provider="google_genai",
        temperature=0.3,
    )

    from app.ai.graph import StockAnalysisAgent

    graph = StockAnalysisAgent(llm=llm)
    logger.info("Agent graph loaded: %s", graph.name)

    # 3. Run analysis
    logger.info("Step 3: Running analysis for %s...", SAMPLE_STOCK["ticker"])
    result = graph.run({
        "stock_data": SAMPLE_STOCK,
        "system_prompt": system_prompt,
        "analysis_prompt": analysis_prompt,
    })

    # 4. Print results
    logger.info("Step 4: Results")
    logger.info("Success: %s", result.success)
    logger.info("Graph name: %s", result.graph_name)

    if result.success:
        logger.info("Recommendation: %s", result.data.get("recommendation"))
        logger.info("Confidence: %s", result.data.get("confidence"))
        logger.info("Reasoning: %s", result.data.get("reasoning", "")[:200])
        logger.info("Key factors: %s", result.data.get("key_factors"))
        logger.info("Risks: %s", result.data.get("risks"))
    else:
        logger.error("Error: %s", result.error)
        if isinstance(result.data, dict) and "raw" in result.data:
            logger.error("Raw LLM response:\n%s", result.data["raw"])
        sys.exit(1)

    logger.info("=== Gemini Test Passed ===")


if __name__ == "__main__":
    test_gemini_analysis_pipeline()

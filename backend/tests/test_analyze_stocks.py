"""Integration test for stock analysis pipeline.

Run: cd backend && python -m pytest tests/test_analyze_stocks.py -v -s
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_FIXTURES_DIR = Path(__file__).parent / "fixtures"

with open(_FIXTURES_DIR / "sample_stock_detail.json") as f:
    SAMPLE_STOCK = json.load(f)


def test_analysis_pipeline() -> None:
    """Test the full analysis pipeline with a single stock."""
    logger.info("=== Stock Analysis Integration Test ===")

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

    # 2. Test agent graph
    logger.info("Step 2: Loading agent graph...")
    from app.ai.factory import AgentFactory

    graph = AgentFactory.get("stock_analysis", output_model=strategy.get_output_model())
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
        # Print raw response for debugging
        if isinstance(result.data, dict) and "raw" in result.data:
            logger.error("Raw LLM response:\n%s", result.data["raw"])
        sys.exit(1)

    logger.info("=== Test Passed ===")


if __name__ == "__main__":
    test_analysis_pipeline()

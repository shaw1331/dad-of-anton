from __future__ import annotations

import logging
from typing import Any

from app.ai.factory import AgentFactory
from app.stock_analyser.analysis.factory import AnalysisFactory

logger = logging.getLogger(__name__)


class AnalyzeStocksTask:
    """Analyzes stocks using AI agent graphs and analysis strategies.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "analyze_stocks"

    def run(self, ctx: Any) -> None:
        scrape_output = ctx.get_output("scrape_stocks")
        if not scrape_output:
            raise Exception("No scraped stocks found. Run ScrapeStocksTask first.")

        stocks = scrape_output["stocks"]
        index = scrape_output["index"]
        strategy_name = ctx.get_input("strategy") or "value_investing"

        logger.info("Starting analysis for %d stocks in %s using '%s' strategy",
                     len(stocks), index, strategy_name)

        strategy = AnalysisFactory.get(strategy_name)
        graph = AgentFactory.get("stock_analysis", output_model=strategy.get_output_model())

        analyses = []
        for i, stock in enumerate(stocks, 1):
            ticker = stock.get("ticker", "UNKNOWN")
            logger.info("[%d/%d] Analyzing %s...", i, len(stocks), ticker)

            result = graph.run({
                "stock_data": stock,
                "system_prompt": strategy.get_system_prompt(),
                "analysis_prompt": strategy.get_analysis_prompt(stock),
            })

            if result.success:
                recommendation = result.data.get("recommendation", "N/A")
                confidence = result.data.get("confidence", "N/A")
                logger.info("[%d/%d] %s — %s (confidence: %s)",
                            i, len(stocks), ticker, recommendation, confidence)
                analysis = {**result.data, "ticker": ticker, "name": stock.get("name", "")}
                analyses.append(analysis)
            else:
                raise Exception(f"Analysis failed for {ticker}: {result.error}")

        logger.info("Analysis complete: %d/%d stocks analyzed successfully",
                     len(analyses), len(stocks))

        ctx.set_output(self.name, {
            "index": index,
            "strategy": strategy_name,
            "analyses": analyses,
            "total_analyzed": len(analyses),
        })

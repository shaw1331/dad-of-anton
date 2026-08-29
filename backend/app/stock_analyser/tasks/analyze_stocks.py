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

        strategy = AnalysisFactory.get(strategy_name)
        graph = AgentFactory.get("stock_analysis")

        analyses = []
        for stock in stocks:
            try:
                result = graph.run({
                    "stock_data": stock,
                    "system_prompt": strategy.get_system_prompt(),
                    "analysis_prompt": strategy.get_analysis_prompt(stock),
                })

                if result.success:
                    analyses.append(result.data)
                else:
                    logger.warning("Analysis failed for %s: %s", stock.get("ticker"), result.error)
                    analyses.append({
                        "ticker": stock.get("ticker", "UNKNOWN"),
                        "error": result.error,
                    })
            except Exception as e:
                logger.error("Error analyzing %s: %s", stock.get("ticker"), e)
                analyses.append({
                    "ticker": stock.get("ticker", "UNKNOWN"),
                    "error": str(e),
                })

        ctx.set_output(self.name, {
            "index": index,
            "strategy": strategy_name,
            "analyses": analyses,
            "total_analyzed": len(analyses),
        })

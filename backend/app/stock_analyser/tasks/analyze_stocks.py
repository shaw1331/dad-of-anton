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

        # Read Trendlyne data if available
        trendlyne_output = ctx.get_output("scrape_trendlyne")
        trendlyne_map: dict[str, dict] = {}
        if trendlyne_output:
            trendlyne_map = {s["ticker"]: s for s in trendlyne_output.get("stocks", [])}

        # Read analyzed news if available
        news_output = ctx.get_output("analyze_news")
        analyzed_news = news_output.get("analyses", {}) if news_output else {}

        logger.info("Starting analysis for %d stocks in %s using '%s' strategy",
                     len(stocks), index, strategy_name)

        strategy = AnalysisFactory.get(strategy_name)
        graph = AgentFactory.get("stock_analysis", output_model=strategy.get_output_model())

        analyses = []
        for i, stock in enumerate(stocks, 1):
            ticker = stock.get("ticker", "UNKNOWN")
            stock_news = analyzed_news.get(ticker, [])
            stock_with_tl = {**stock, "trendlyne": trendlyne_map.get(ticker)}
            logger.info("[%d/%d] Analyzing %s...", i, len(stocks), ticker)

            try:
                result = graph.run({
                    "stock_data": stock_with_tl,
                    "system_prompt": strategy.get_system_prompt(),
                    "analysis_prompt": strategy.get_analysis_prompt(stock_with_tl, stock_news),
                })

                if result.success:
                    recommendation = result.data.get("recommendation", "N/A")
                    confidence = result.data.get("confidence", "N/A")
                    logger.info("[%d/%d] %s — %s (confidence: %s)",
                                i, len(stocks), ticker, recommendation, confidence)
                    analysis = {**result.data, "ticker": ticker, "name": stock.get("name", "")}
                    analyses.append(analysis)
                else:
                    logger.error("[%d/%d] Analysis failed for %s: %s",
                                 i, len(stocks), ticker, result.error)
                    analyses.append({
                        "ticker": ticker,
                        "name": stock.get("name", ""),
                        "error": result.error,
                    })
            except Exception as e:
                logger.error("[%d/%d] Analysis error for %s: %s",
                             i, len(stocks), ticker, str(e))
                analyses.append({
                    "ticker": ticker,
                    "name": stock.get("name", ""),
                    "error": str(e),
                })

        logger.info("Analysis complete: %d/%d stocks analyzed successfully",
                     len([a for a in analyses if "error" not in a]), len(stocks))

        ctx.set_output(self.name, {
            "index": index,
            "strategy": strategy_name,
            "analyses": analyses,
            "total_analyzed": len(analyses),
        })

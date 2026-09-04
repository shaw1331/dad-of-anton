from __future__ import annotations

import logging
from typing import Any

from app.ai.factory import AgentFactory
from app.ai.models import NewsAnalysisResult

logger = logging.getLogger(__name__)

NEWS_SYSTEM_PROMPT = """\
You are a financial news analyst for the Indian stock market.
Analyze the provided news articles and for each one:
1. Generate a detailed 2-3 paragraph summary from the full content
2. Grade the impact on the company's stock:
   - CRITICAL: M&A, regulatory action, fraud, bankruptcy, major legal issues
   - HIGH: Earnings surprises, guidance changes, CEO/CFO changes, large contracts
   - MEDIUM: Sector trends, analyst upgrades/downgrades, moderate news
   - LOW: Routine announcements, minor updates, routine disclosures
3. Determine trader sentiment: bullish, bearish, or neutral
4. Explain your reasoning for the impact grade

Be concise but thorough. Focus on what matters to traders and investors."""


class AnalyzeNewsTask:
    """Analyzes news articles using the NewsAnalysisAgent LangGraph.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "analyze_news"

    def run(self, ctx: Any) -> None:
        enable_news = ctx.get_input("enable_news")
        if not enable_news:
            ctx.set_output(self.name, {"analyses": {}, "total_analyzed": 0})
            return

        news_output = ctx.get_output("scrape_news")
        if not news_output:
            raise Exception("No news data found. Run ScrapeNewsTask first.")

        news = news_output["news"]
        graph = AgentFactory.get("news_analysis", output_model=NewsAnalysisResult)

        all_analyses: dict[str, list[dict]] = {}
        total = 0

        for i, (ticker, articles) in enumerate(news.items(), 1):
            if not articles:
                all_analyses[ticker] = []
                continue

            logger.info("[%d/%d] Analyzing %d news articles for %s...",
                        i, len(news), len(articles), ticker)

            result = graph.run({
                "ticker": ticker,
                "articles": articles,
                "system_prompt": NEWS_SYSTEM_PROMPT,
            })

            if result.success:
                analyzed = result.data.get("articles", [])
                all_analyses[ticker] = analyzed
                total += len(analyzed)
                logger.info("[%d/%d] %s — analyzed %d articles",
                            i, len(news), ticker, len(analyzed))
            else:
                logger.error("[%d/%d] News analysis failed for %s: %s",
                             i, len(news), ticker, result.error)
                all_analyses[ticker] = []

        logger.info("News analysis complete: %d articles across %d stocks",
                     total, len(news))

        ctx.set_output(self.name, {
            "analyses": all_analyses,
            "total_analyzed": total,
        })

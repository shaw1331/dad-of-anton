from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ai.factory import AgentFactory
from app.ai.models import NewsImpact, NewsAnalysisResult

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "analysis" / "prompts"

_IMPACT_RANK = {
    NewsImpact.CRITICAL: 0,
    NewsImpact.HIGH: 1,
    NewsImpact.MEDIUM: 2,
    NewsImpact.LOW: 3,
}


def _parse_pub_date(date_str: str) -> datetime:
    """Parse pub_date string to UTC datetime for recency comparison."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return datetime.min.replace(tzinfo=timezone.utc)


def _select_top_n(articles: list[dict], n: int) -> list[dict]:
    """Select top n articles by impact (highest first), then recency (most recent first)."""
    def sort_key(article: dict) -> tuple[int, datetime]:
        impact = article.get("impact", "low")
        try:
            impact_val = _IMPACT_RANK[NewsImpact(impact)]
        except ValueError:
            impact_val = _IMPACT_RANK[NewsImpact.LOW]
        return (impact_val, _parse_pub_date(article.get("pub_date", "")))

    sorted_articles = sorted(articles, key=sort_key)
    return sorted_articles[:n]


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
        num_articles = ctx.get_input("num_news_articles") or 3
        graph = AgentFactory.get("news_analysis", output_model=NewsAnalysisResult)
        system_prompt = (_PROMPT_DIR / "news_analysis.md").read_text()

        all_analyses: dict[str, list[dict]] = {}
        total = 0

        for i, (ticker, articles) in enumerate(news.items(), 1):
            if not articles:
                all_analyses[ticker] = []
                continue

            logger.info("[%d/%d] Analyzing %d news articles for %s...",
                        i, len(news), len(articles), ticker)

            try:
                result = graph.run({
                    "ticker": ticker,
                    "articles": articles,
                    "system_prompt": system_prompt,
                })

                if result.success:
                    analyzed = result.data.get("articles", [])
                    selected = _select_top_n(analyzed, num_articles)
                    all_analyses[ticker] = selected
                    total += len(selected)
                    logger.info("[%d/%d] %s — analyzed %d, selected top %d",
                                i, len(news), ticker, len(analyzed), len(selected))
                else:
                    logger.error("[%d/%d] News analysis failed for %s: %s",
                                 i, len(news), ticker, result.error)
                    all_analyses[ticker] = []
            except Exception:
                logger.exception("[%d/%d] %s — news analysis crashed", i, len(news), ticker)
                all_analyses[ticker] = []

        logger.info("News analysis complete: %d articles across %d stocks",
                     total, len(news))

        ctx.set_output(self.name, {
            "analyses": all_analyses,
            "total_analyzed": total,
        })

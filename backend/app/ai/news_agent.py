from __future__ import annotations

import logging
from typing import Any

import trafilatura
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.ai.factory import AgentFactory
from app.ai.interfaces import AgentGraph
from app.ai.models import AgentResult, AnalyzedNewsArticle

logger = logging.getLogger(__name__)


class NewsAnalysisAgent(AgentGraph):
    """LangGraph agent for news analysis using an injected LLM.

    Fetches full article content via trafilatura, then uses the LLM
    to summarize, grade impact, and determine trader sentiment.
    Processes articles one at a time to stay within LLM context limits.
    """

    name = "news_analysis"

    def __init__(self, llm: BaseChatModel, output_model: type[BaseModel]) -> None:
        self.llm = llm
        self.output_model = output_model

    def _fetch_content(self, url: str) -> str:
        """Fetch full article content from a URL using trafilatura."""
        if not url:
            return ""
        try:
            downloaded = trafilatura.fetch_url(url)
            return trafilatura.extract(downloaded) or ""
        except Exception:
            logger.warning("Failed to fetch content for %s", url)
            return ""

    def _analyze_single(self, article: dict, ticker: str, system_prompt: str) -> dict:
        """Analyze a single article by fetching content and calling LLM."""
        full_content = self._fetch_content(article.get("url", ""))
        summary = article.get("summary", "")

        content_text = full_content if full_content else "[Could not extract content]"

        structured_llm = self.llm.with_structured_output(AnalyzedNewsArticle)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"Analyze this news article for {ticker}:\n\n"
                f"Source: {article.get('source', 'Unknown')}\n"
                f"Date: {article.get('pub_date', 'Unknown')}\n"
                f"URL: {article.get('url', 'N/A')}\n"
                f"Summary: {summary}\n"
                f"Full Content: {content_text}"
            )),
        ]
        result = structured_llm.invoke(messages)
        return result.model_dump()

    def run(self, input_data: dict[str, Any]) -> AgentResult:
        ticker = input_data["ticker"]
        articles = input_data["articles"]
        system_prompt = input_data["system_prompt"]

        analyzed = []
        for article in articles:
            try:
                result = self._analyze_single(article, ticker, system_prompt)
                analyzed.append(result)
            except Exception:
                logger.warning("Failed to analyze article %s for %s",
                               article.get("url", ""), ticker)

        return AgentResult(
            success=True,
            data={"articles": analyzed, "ticker": ticker,
                  "total_articles": len(analyzed)},
            error=None,
            graph_name=self.name,
        )


AgentFactory.register("news_analysis", NewsAnalysisAgent)

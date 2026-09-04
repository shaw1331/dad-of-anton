from __future__ import annotations

import logging
from typing import Any, Optional, TypedDict

import trafilatura
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.ai.factory import AgentFactory
from app.ai.interfaces import AgentGraph
from app.ai.models import AgentResult, NewsAnalysisResult

logger = logging.getLogger(__name__)


class NewsAnalysisState(TypedDict):
    """State for the news analysis LangGraph graph."""

    ticker: str
    articles: list[dict]
    fetched_articles: list[dict]
    system_prompt: str
    raw_response: str
    parsed_analysis: Optional[BaseModel]


class NewsAnalysisAgent(AgentGraph):
    """LangGraph agent for news analysis using an injected LLM.

    Fetches full article content via trafilatura, then uses the LLM
    to summarize, grade impact, and determine trader sentiment.
    """

    name = "news_analysis"

    def __init__(self, llm: BaseChatModel, output_model: type[BaseModel]) -> None:
        self.llm = llm
        self.output_model = output_model
        self._graph = self._build_graph()

    def _fetch_content(self, articles: list[dict]) -> list[dict]:
        """Fetch full article content from URLs using trafilatura."""
        fetched = []
        for article in articles:
            url = article.get("url", "")
            if not url:
                fetched.append({**article, "full_content": ""})
                continue

            try:
                downloaded = trafilatura.fetch_url(url)
                content = trafilatura.extract(downloaded) if downloaded else ""
                fetched.append({**article, "full_content": content or ""})
            except Exception:
                logger.warning("Failed to fetch content for %s", url)
                fetched.append({**article, "full_content": ""})

        return fetched

    def _build_graph(self):
        structured_llm = self.llm.with_structured_output(self.output_model)

        def fetch_content_node(state: NewsAnalysisState) -> dict:
            fetched = self._fetch_content(state["articles"])
            return {"fetched_articles": fetched}

        def analyze_node(state: NewsAnalysisState) -> dict:
            articles_text = self._format_articles_for_prompt(state["fetched_articles"])

            messages = [
                SystemMessage(content=state["system_prompt"]),
                HumanMessage(content=(
                    f"Analyze the following news articles for {state['ticker']}:\n\n"
                    f"{articles_text}"
                )),
            ]
            result = structured_llm.invoke(messages)
            return {
                "raw_response": result.model_dump_json(),
                "parsed_analysis": result,
            }

        graph = StateGraph(NewsAnalysisState)
        graph.add_node("fetch_content", fetch_content_node)
        graph.add_node("analyze", analyze_node)
        graph.set_entry_point("fetch_content")
        graph.add_edge("fetch_content", "analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def _format_articles_for_prompt(self, articles: list[dict]) -> str:
        """Format fetched articles into a readable prompt section."""
        parts = []
        for i, article in enumerate(articles, 1):
            content = article.get("full_content", "")
            summary = article.get("summary", "")
            parts.append(
                f"Article {i}:\n"
                f"Source: {article.get('source', 'Unknown')}\n"
                f"Date: {article.get('pub_date', 'Unknown')}\n"
                f"URL: {article.get('url', 'N/A')}\n"
                f"Summary: {summary}\n"
                f"Full Content: {content if content else '[Could not extract content]'}"
            )
        return "\n\n".join(parts)

    def run(self, input_data: dict[str, Any]) -> AgentResult:
        initial_state: NewsAnalysisState = {
            "ticker": input_data["ticker"],
            "articles": input_data["articles"],
            "fetched_articles": [],
            "system_prompt": input_data["system_prompt"],
            "raw_response": "",
            "parsed_analysis": None,
        }

        result = self._graph.invoke(initial_state)

        parsed = result["parsed_analysis"]
        return AgentResult(
            success=parsed is not None,
            data=parsed.model_dump() if parsed else {"raw": result["raw_response"]},
            error=None if parsed else "Failed to parse LLM response",
            graph_name=self.name,
        )


AgentFactory.register("news_analysis", NewsAnalysisAgent)

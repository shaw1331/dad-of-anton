from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional, TypedDict

logger = logging.getLogger(__name__)

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.ai.factory import AgentFactory
from app.ai.interfaces import AgentGraph
from app.ai.models import AgentResult


class StockAnalysisState(TypedDict):
    """State for the stock analysis LangGraph graph."""

    stock_data: dict
    system_prompt: str
    analysis_prompt: str
    raw_response: str
    parsed_analysis: Optional[dict]


class StockAnalysisAgent(AgentGraph):
    """LangGraph agent for stock analysis using an injected LLM."""

    name = "stock_analysis"

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm
        self._graph = self._build_graph()

    def _build_graph(self):
        def analyze_node(state: StockAnalysisState) -> dict:
            messages = [
                SystemMessage(content=state["system_prompt"]),
                HumanMessage(content=state["analysis_prompt"]),
            ]
            response = self.llm.invoke(messages)

            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError:
                logger.debug("Raw LLM response:\n%s", response.content[:500])
                parsed = _extract_json(response.content)
                if parsed is None:
                    logger.warning("Failed to parse LLM response for %s",
                                   state["stock_data"].get("ticker"))

            return {
                "raw_response": response.content,
                "parsed_analysis": parsed,
            }

        graph = StateGraph(StockAnalysisState)
        graph.add_node("analyze", analyze_node)
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def run(self, input_data: dict[str, Any]) -> AgentResult:
        initial_state = {
            "stock_data": input_data["stock_data"],
            "system_prompt": input_data["system_prompt"],
            "analysis_prompt": input_data["analysis_prompt"],
            "raw_response": "",
            "parsed_analysis": None,
        }

        result = self._graph.invoke(initial_state)

        return AgentResult(
            success=result["parsed_analysis"] is not None,
            data=result["parsed_analysis"] or {"raw": result["raw_response"]},
            error=None if result["parsed_analysis"] else "Failed to parse LLM response",
            graph_name=self.name,
        )


AgentFactory.register("stock_analysis", StockAnalysisAgent)


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from text, handling markdown code blocks and trailing text."""
    # Try markdown code blocks first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting from first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None

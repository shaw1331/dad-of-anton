from __future__ import annotations

import json
from typing import Any, TypedDict

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
    parsed_analysis: dict | None


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
                parsed = None

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

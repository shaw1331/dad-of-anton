from __future__ import annotations

import logging
from typing import Any, Optional, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.ai.audit import build_audit, invocation_started
from app.ai.factory import AgentFactory
from app.ai.interfaces import AgentGraph
from app.ai.models import AgentResult

logger = logging.getLogger(__name__)


class StockAnalysisState(TypedDict):
    """State for the stock analysis LangGraph graph."""

    stock_data: dict
    system_prompt: str
    analysis_prompt: str
    raw_response: str
    parsed_analysis: Optional[BaseModel]


class StockAnalysisAgent(AgentGraph):
    """LangGraph agent for stock analysis using an injected LLM."""

    name = "stock_analysis"

    def __init__(self, llm: BaseChatModel, output_model: type[BaseModel]) -> None:
        self.llm = llm
        self.output_model = output_model
        self._graph = self._build_graph()

    def _build_graph(self):
        structured_llm = self.llm.with_structured_output(self.output_model)

        def analyze_node(state: StockAnalysisState) -> dict:
            messages = [
                SystemMessage(content=state["system_prompt"]),
                HumanMessage(content=state["analysis_prompt"]),
            ]
            result = structured_llm.invoke(messages)
            return {
                "raw_response": result.model_dump_json(),
                "parsed_analysis": result,
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

        started_at = invocation_started()
        try:
            result = self._graph.invoke(initial_state)
            parsed = result["parsed_analysis"]
            data = parsed.model_dump() if parsed else {"raw": result["raw_response"]}
            error = None if parsed else "Failed to parse LLM response"
            return AgentResult(
                success=parsed is not None,
                data=data,
                error=error,
                graph_name=self.name,
                audits=[build_audit(
                    agent_name=self.name,
                    context=getattr(self, "audit_context", None),
                    prompt_version=input_data.get("prompt_version", "unversioned"),
                    schema_version=self.output_model.__name__,
                    system_prompt=initial_state["system_prompt"],
                    analysis_prompt=initial_state["analysis_prompt"],
                    started_at=started_at,
                    output=data,
                    error=error,
                )],
            )
        except Exception as error:
            message = str(error)
            return AgentResult(
                success=False,
                data=None,
                error=message,
                graph_name=self.name,
                audits=[build_audit(
                    agent_name=self.name,
                    context=getattr(self, "audit_context", None),
                    prompt_version=input_data.get("prompt_version", "unversioned"),
                    schema_version=self.output_model.__name__,
                    system_prompt=initial_state["system_prompt"],
                    analysis_prompt=initial_state["analysis_prompt"],
                    started_at=started_at,
                    error=message,
                )],
            )


AgentFactory.register("stock_analysis", StockAnalysisAgent)

from app.ai.exceptions import AnalysisError, ConfigError, GraphError
from app.ai.factory import AgentFactory
from app.ai.interfaces import AgentGraph
from app.ai.models import (
    AgentConfig,
    AgentResult,
    AnalyzedNewsArticle,
    NewsAnalysisResult,
    NewsImpact,
)
import app.ai.graph  # noqa: F401 — register StockAnalysisAgent with factory

__all__ = [
    "AnalysisError",
    "AgentConfig",
    "AgentFactory",
    "AgentGraph",
    "AgentResult",
    "AnalyzedNewsArticle",
    "ConfigError",
    "GraphError",
    "NewsAnalysisResult",
    "NewsImpact",
    "StockAnalysisAgent",
]


def __getattr__(name: str):
    if name == "StockAnalysisAgent":
        from app.ai.graph import StockAnalysisAgent

        return StockAnalysisAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

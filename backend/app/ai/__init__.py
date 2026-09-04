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
import app.ai.news_agent  # noqa: F401 — register NewsAnalysisAgent with factory

__all__ = [
    "AnalysisError",
    "AgentConfig",
    "AgentFactory",
    "AgentGraph",
    "AgentResult",
    "AnalyzedNewsArticle",
    "ConfigError",
    "GraphError",
    "NewsAnalysisAgent",
    "NewsAnalysisResult",
    "NewsImpact",
    "StockAnalysisAgent",
]


def __getattr__(name: str):
    if name == "StockAnalysisAgent":
        from app.ai.graph import StockAnalysisAgent

        return StockAnalysisAgent
    if name == "NewsAnalysisAgent":
        from app.ai.news_agent import NewsAnalysisAgent

        return NewsAnalysisAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

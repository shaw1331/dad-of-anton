from __future__ import annotations

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class AgentAuditContext(BaseModel):
    """Static LLM configuration attached by AgentFactory."""

    provider: str
    model: str
    temperature: float


class AgentAudit(BaseModel):
    """Traceable record for one LLM invocation."""

    agent_name: str
    provider: str
    model: str
    temperature: float
    prompt_version: str
    schema_version: str
    latency_ms: int
    retry_count: int = 0
    system_prompt: str
    analysis_prompt: str
    output_citations: list[str] = Field(default_factory=list)
    error: str | None = None


class AgentResult(BaseModel, Generic[T]):
    """Generic result wrapper for agent graph execution."""

    success: bool
    data: T | None = None
    error: str | None = None
    graph_name: str
    audits: list[AgentAudit] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "ollama"
    model: str = "llama3"
    temperature: float = 0.3
    timeout: int = 120


class NewsImpact(str, Enum):
    """Grades news articles by potential market impact."""

    CRITICAL = "critical"  # M&A, regulatory action, fraud, bankruptcy
    HIGH = "high"  # Earnings surprises, guidance changes, CEO changes
    MEDIUM = "medium"  # Sector trends, analyst upgrades/downgrades
    LOW = "low"  # Routine announcements, minor updates


class AnalyzedNewsArticle(BaseModel):
    """A news article processed by the NewsAnalysisAgent."""

    ticker: str
    news_id: str
    url: str
    source: str
    pub_date: str
    raw_summary: str
    detailed_summary: str
    impact: NewsImpact
    impact_reasoning: str
    trader_sentiment: str  # "bullish" | "bearish" | "neutral"


class NewsAnalysisResult(BaseModel):
    """Output of the NewsAnalysisAgent for a single ticker."""

    articles: list[AnalyzedNewsArticle]
    ticker: str
    total_articles: int
    impact_distribution: dict[str, int]

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class AgentResult(BaseModel, Generic[T]):
    """Generic result wrapper for agent graph execution."""

    success: bool
    data: T | None = None
    error: str | None = None
    graph_name: str


class AgentConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "ollama"
    model: str = "llama3"
    temperature: float = 0.3
    timeout: int = 120

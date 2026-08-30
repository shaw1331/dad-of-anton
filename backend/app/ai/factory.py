from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from app.ai.exceptions import ConfigError
from app.ai.interfaces import AgentGraph


class AgentFactory:
    """Factory for creating agent graph instances.

    Graphs are registered by name (e.g., "stock_analysis").
    Uses LangChain's init_chat_model to create a provider-agnostic LLM
    based on settings (LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE).
    """

    _graphs: dict[str, Type[AgentGraph]] = {}

    @classmethod
    def register(cls, name: str, graph_cls: Type[AgentGraph]) -> None:
        """Register an AgentGraph implementation."""
        cls._graphs[name] = graph_cls

    @classmethod
    def get(cls, name: str, output_model: type[BaseModel] | None = None) -> AgentGraph:
        """Get an AgentGraph instance with configured LLM.

        Uses init_chat_model to create provider-agnostic LLM.
        Provider/model configured via LLM_PROVIDER and LLM_MODEL env vars.

        Args:
            name: The registered graph name.
            output_model: Optional Pydantic model for structured LLM output.

        Returns:
            An AgentGraph instance with an LLM attached.

        Raises:
            ConfigError: If no graph is registered for the name.
        """
        from langchain.chat_models import init_chat_model

        from app.core.config import settings

        kwargs = {
            "model": settings.LLM_MODEL,
            "model_provider": settings.LLM_PROVIDER,
            "temperature": settings.LLM_TEMPERATURE,
        }

        if settings.LLM_PROVIDER == "google_genai":
            kwargs["google_api_key"] = settings.GOOGLE_API_KEY

        llm = init_chat_model(**kwargs)

        graph_cls = cls._graphs.get(name)
        if graph_cls is None:
            available = list(cls._graphs.keys())
            raise ConfigError(
                f"No AgentGraph registered for '{name}'. "
                f"Available graphs: {available}"
            )

        if output_model is not None:
            return graph_cls(llm=llm, output_model=output_model)
        return graph_cls(llm=llm)

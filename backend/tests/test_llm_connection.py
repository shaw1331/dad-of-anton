from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.core.config import settings


@pytest.fixture
def llm():
    from langchain.chat_models import init_chat_model

    kwargs = {
        "model": settings.LLM_MODEL,
        "model_provider": settings.LLM_PROVIDER,
        "temperature": 0,
    }
    if settings.LLM_PROVIDER == "google_genai":
        kwargs["google_api_key"] = settings.GOOGLE_API_KEY
    elif settings.LLM_PROVIDER == "openai":
        kwargs["api_key"] = settings.OPENAI_API_KEY
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
    elif settings.LLM_PROVIDER == "anthropic":
        kwargs["api_key"] = settings.ANTHROPIC_API_KEY
    elif settings.LLM_PROVIDER == "groq":
        kwargs["api_key"] = settings.GROQ_API_KEY
    elif settings.LLM_PROVIDER == "openrouter":
        kwargs["api_key"] = settings.OPENROUTER_API_KEY
    return init_chat_model(**kwargs)


def test_llm_invocation(llm):
    result = llm.invoke("Say hello in one word.")
    assert result.content
    assert isinstance(result.content, str)
    assert len(result.content.strip()) > 0


class OneWord(BaseModel):
    word: str


def test_llm_structured_output(llm):
    structured_llm = llm.with_structured_output(OneWord)
    result = structured_llm.invoke("Respond with exactly one word: hello")
    assert isinstance(result, OneWord)
    assert len(result.word.strip()) > 0

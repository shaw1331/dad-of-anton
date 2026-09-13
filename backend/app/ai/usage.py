from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from app.ai.models import AgentAudit


def tokens_from_message(message: BaseMessage | Any | None) -> tuple[int, int, int]:
    if message is None:
        return (0, 0, 0)

    meta = getattr(message, "usage_metadata", None)
    if meta is not None:
        return (meta.get("input_tokens", 0) or 0,
                meta.get("output_tokens", 0) or 0,
                meta.get("total_tokens", 0) or 0)

    resp_meta = getattr(message, "response_metadata", {}) or {}
    for key in ("token_usage", "usage"):
        usage = resp_meta.get(key)
        if usage and isinstance(usage, dict):
            inp = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
            out = usage.get("output_tokens") or usage.get("completion_tokens") or 0
            total = usage.get("total_tokens") or (inp + out)
            return (int(inp), int(out), int(total))

    return (0, 0, 0)


def invoke_structured(
    llm: BaseChatModel,
    output_model: type[BaseModel],
    messages: list[BaseMessage],
) -> tuple[BaseModel | None, tuple[int, int, int]]:
    bound = llm.with_structured_output(output_model, include_raw=True)
    out = bound.invoke(messages)
    if isinstance(out, dict):
        parsed = out.get("parsed")
        return parsed, tokens_from_message(out.get("raw"))
    if isinstance(out, output_model):
        return out, (0, 0, 0)
    return None, (0, 0, 0)


def rollup_token_usage(audits: list[AgentAudit]) -> dict[str, Any]:
    if not audits:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "model": None,
            "duration_s": 0.0,
            "calls": 0,
        }
    total_latency = sum(a.latency_ms for a in audits)
    return {
        "input_tokens": sum(a.input_tokens for a in audits),
        "output_tokens": sum(a.output_tokens for a in audits),
        "total_tokens": sum(a.total_tokens for a in audits),
        "model": audits[0].model,
        "duration_s": round(total_latency / 1000, 1),
        "calls": len(audits),
    }
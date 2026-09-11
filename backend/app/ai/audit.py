from __future__ import annotations

from time import perf_counter
from typing import Any

from app.ai.models import AgentAudit, AgentAuditContext


def invocation_started() -> float:
    return perf_counter()


def build_audit(
    *,
    agent_name: str,
    context: AgentAuditContext | None,
    prompt_version: str,
    schema_version: str,
    system_prompt: str,
    analysis_prompt: str,
    started_at: float,
    output: Any = None,
    error: str | None = None,
) -> AgentAudit:
    metadata = context or AgentAuditContext(provider="unknown", model="unknown", temperature=0.0)
    return AgentAudit(
        agent_name=agent_name,
        provider=metadata.provider,
        model=metadata.model,
        temperature=metadata.temperature,
        prompt_version=prompt_version,
        schema_version=schema_version,
        latency_ms=round((perf_counter() - started_at) * 1000),
        system_prompt=system_prompt,
        analysis_prompt=analysis_prompt,
        output_citations=extract_citations(output),
        error=error,
    )


def extract_citations(value: Any) -> list[str]:
    """Extract evidence-reference fields from structured agent output."""
    refs: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                if key in {"evidence_refs", "counter_evidence_refs"} and isinstance(nested, list):
                    refs.update(reference for reference in nested if isinstance(reference, str))
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    if hasattr(value, "model_dump"):
        value = value.model_dump()
    visit(value)
    return sorted(refs)

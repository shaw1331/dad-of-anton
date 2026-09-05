"""Shared test utilities."""
from __future__ import annotations

from app.workflow.base_workflow_context import BaseWorkflowContext


def make_context(input=None, outputs=None) -> BaseWorkflowContext:
    ctx = BaseWorkflowContext(input=input or {})
    if outputs:
        for task_name, value in outputs.items():
            ctx.set_output(task_name, value)
    return ctx

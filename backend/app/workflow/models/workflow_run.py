from __future__ import annotations

from app.models.base import BaseModel


class WorkflowRun(BaseModel):
    workflow_name: str
    status: str
    current_task_index: int
    total_tasks: int
    error: str | None = None
    input: dict | None = None

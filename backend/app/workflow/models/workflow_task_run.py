from __future__ import annotations

from app.models.base import BaseModel


class WorkflowTaskRun(BaseModel):
    workflow_run_id: str
    task_name: str
    task_index: int
    status: str
    error: str | None = None
    output: dict | None = None
    started_at: str | None = None
    completed_at: str | None = None

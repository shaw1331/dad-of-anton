from __future__ import annotations

from datetime import datetime, timezone

from app.core.database import supabase
from app.workflow.models.workflow_task_run import WorkflowTaskRun


class WorkflowTaskRunRepository:
    def create(self, task_run: WorkflowTaskRun) -> None:
        supabase.table("workflow_task_runs").insert(task_run.model_dump()).execute()

    def get(self, workflow_run_id: str, task_index: int) -> WorkflowTaskRun:
        result = supabase.table("workflow_task_runs") \
            .select("*") \
            .eq("workflow_run_id", workflow_run_id) \
            .eq("task_index", task_index) \
            .single() \
            .execute()
        return WorkflowTaskRun.model_validate(result.data)

    def list_by_run(self, workflow_run_id: str) -> list[WorkflowTaskRun]:
        result = supabase.table("workflow_task_runs") \
            .select("*") \
            .eq("workflow_run_id", workflow_run_id) \
            .order("task_index") \
            .execute()
        return [WorkflowTaskRun.model_validate(row) for row in result.data]

    def update_status(self, task_run_id: str, status: str, error: str | None = None) -> None:
        data: dict = {
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if error is not None:
            data["error"] = error
        supabase.table("workflow_task_runs").update(data).eq("id", task_run_id).execute()

    def update_running(self, task_run_id: str) -> None:
        supabase.table("workflow_task_runs").update({
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", task_run_id).execute()

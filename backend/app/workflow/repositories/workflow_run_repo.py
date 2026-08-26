from __future__ import annotations

from datetime import datetime, timezone

from app.core.database import supabase
from app.workflow.models.workflow_run import WorkflowRun


class WorkflowRunRepository:
    def create(self, run: WorkflowRun) -> None:
        supabase.table("workflow_runs").insert(run.model_dump()).execute()

    def get(self, run_id: str) -> WorkflowRun:
        result = supabase.table("workflow_runs").select("*").eq("id", run_id).single().execute()
        return WorkflowRun.model_validate(result.data)

    def update_status(self, run_id: str, status: str, error: str | None = None) -> None:
        data: dict = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if error is not None:
            data["error"] = error
        supabase.table("workflow_runs").update(data).eq("id", run_id).execute()

    def list_all(self) -> list[WorkflowRun]:
        result = supabase.table("workflow_runs").select("*").order("created_at", desc=True).execute()
        return [WorkflowRun.model_validate(row) for row in result.data]

    def update_progress(self, run_id: str, current_task_index: int) -> None:
        supabase.table("workflow_runs").update({
            "current_task_index": current_task_index,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", run_id).execute()

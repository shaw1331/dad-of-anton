from __future__ import annotations

from datetime import datetime, timezone

from app.core.database import get_supabase_client
from app.workflow.models.workflow_run import WorkflowRun


class WorkflowRunRepository:
    def create(self, run: WorkflowRun) -> None:
        supabase = get_supabase_client()
        supabase.table("workflow_runs").insert(run.model_dump(mode="json")).execute()

    def get(self, run_id: str) -> WorkflowRun:
        supabase = get_supabase_client()
        result = supabase.table("workflow_runs").select("*").eq("id", run_id).single().execute()
        return WorkflowRun.model_validate(result.data)

    def update_status(self, run_id: str, status: str, error: str | None = None) -> None:
        supabase = get_supabase_client()
        data: dict = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if error is not None:
            data["error"] = error
        supabase.table("workflow_runs").update(data).eq("id", run_id).execute()

    def list_page(self, limit: int, offset: int) -> list[WorkflowRun]:
        supabase = get_supabase_client()
        result = (
            supabase.table("workflow_runs")
            .select("id,workflow_name,status,trigger_type,current_task_index,total_tasks,error,created_at,updated_at")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        rows = result.data or []
        return [WorkflowRun.model_validate(row) for row in rows]

    def update_progress(self, run_id: str, current_task_index: int) -> None:
        supabase = get_supabase_client()
        supabase.table("workflow_runs").update({
            "current_task_index": current_task_index,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", run_id).execute()

    def update_output(self, run_id: str, output: dict) -> None:
        supabase = get_supabase_client()
        supabase.table("workflow_runs").update({
            "output": output,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", run_id).execute()

    def delete(self, run_id: str) -> None:
        supabase = get_supabase_client()
        supabase.table("workflow_runs").delete().eq("id", run_id).execute()

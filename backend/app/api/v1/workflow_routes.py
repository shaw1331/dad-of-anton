from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.workflow.workflow_orchestrator_v1.workflow_orchestrator import WorkflowOrchestrator
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

router = APIRouter(prefix="/workflows", tags=["workflows"])

orchestrator = WorkflowOrchestrator()


class TriggerRequest(BaseModel):
    input: dict[str, Any] = {}


@router.get("")
def list_workflows():
    return [
        {
            "name": config.name,
            "description": config.description,
            "task_count": len(config.tasks),
            "input_fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "label": f.label,
                    "description": f.description,
                    "required": f.required,
                    "default": f.default,
                    "choices": f.choices,
                }
                for f in config.input_fields
            ],
        }
        for config in WORKFLOWS.values()
    ]


@router.post("/{name}/trigger")
def trigger_workflow(name: str, background_tasks: BackgroundTasks, request: TriggerRequest | None = None):
    input_data = request.input if request else {}
    try:
        run_id = orchestrator.trigger_workflow(name, background_tasks, input_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"run_id": run_id}


@router.get("/runs")
def list_runs():
    from app.workflow.repositories import WorkflowRunRepository

    repo = WorkflowRunRepository()
    runs = repo.list_all()
    return [run.model_dump() for run in runs]


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository

    run_repo = WorkflowRunRepository()
    task_repo = WorkflowTaskRunRepository()

    try:
        run = run_repo.get(run_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    task_runs = task_repo.list_by_run(run_id)
    return {
        **run.model_dump(),
        "task_runs": [tr.model_dump() for tr in task_runs],
    }


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: str):
    try:
        orchestrator.delete_run(run_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

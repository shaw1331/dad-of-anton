# DOA-002: Remove dead orchestrator singleton and wire routes via FastAPI dependency injection

- **Type:** Tech debt / Refactor
- **Priority:** P1
- **Component:** backend / api, workflow
- **Affected files:** `backend/app/workflow/workflow_orchestrator.py`, `backend/app/api/v1/workflow_routes.py`

## Problem

1. **Two orchestrator instances exist.** Commit `d01b517` ("refactor: remove orchestrator singleton from public API") removed the singleton from `app/workflow/__init__.py` exports, but the module-level instance was left behind at `workflow_orchestrator.py:90`:

   ```python
   orchestrator = WorkflowOrchestrator()
   ```

   Meanwhile `workflow_routes.py:10` creates a *second* instance. The one in `workflow_orchestrator.py` is now dead code that still constructs two repositories at import time.

2. **Routes instantiate repositories ad hoc with function-level imports.** `workflow_routes.py:30-36` and `:39-55` do `from app.workflow.repositories import ...` inside the handler bodies and `WorkflowRunRepository()` per request. This defeats testability (nothing can be overridden) and hides the module's real dependencies.

## Fix

- Delete the module-level `orchestrator` in `workflow_orchestrator.py`.
- In `workflow_routes.py`, move all imports to the top and inject the orchestrator and repositories with `Depends(...)`. FastAPI can `Depends` on a class directly (it calls the constructor), which makes `app.dependency_overrides` work in tests (see DOA-010).

## Steps of completion

1. Remove line 90-91 (`orchestrator = WorkflowOrchestrator()`) from `workflow_orchestrator.py`.
2. `grep -rn "workflow_orchestrator import orchestrator"` to confirm nothing imports the deleted name.
3. Refactor `workflow_routes.py`: top-level imports, `Depends(WorkflowOrchestrator)`, `Depends(WorkflowRunRepository)`, `Depends(WorkflowTaskRunRepository)`.
4. Run the app and smoke-test `GET /api/v1/workflows`, `POST /api/v1/workflows/sample/trigger`, `GET /api/v1/workflows/runs`, `GET /api/v1/workflows/runs/{id}`.

## Before / after

**Before** — a dead singleton at `workflow_orchestrator.py:90`; routes hold their own private orchestrator at `workflow_routes.py:10` and build repositories inside handler bodies with local imports.

**After** — exactly one construction path: FastAPI builds (cheap, stateless) instances per request via `Depends`, which is override-friendly for tests, and the dead module-level singleton is gone.

## Changes (diff)

### `backend/app/workflow/workflow_orchestrator.py`

```diff
@@ -85,7 +85,4 @@
         except Exception as e:
             logger.error("Workflow %s failed unexpectedly: %s", run_id, e)
             self.run_repo.update_status(run_id, "failed", f"Unexpected error: {e}")
-
-
-orchestrator = WorkflowOrchestrator()
```

### `backend/app/api/v1/workflow_routes.py`

```diff
@@ -1,56 +1,53 @@
 from __future__ import annotations

-from fastapi import APIRouter, BackgroundTasks, HTTPException
+from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

 from app.workflow.workflow_orchestrator import WorkflowOrchestrator
+from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository
 from app.workflow.workflow_registry import WORKFLOWS

 router = APIRouter(prefix="/workflows", tags=["workflows"])

-orchestrator = WorkflowOrchestrator()
-

 @router.get("")
 def list_workflows():
     return [
         {"name": config.name, "description": config.description, "task_count": len(config.tasks)}
         for config in WORKFLOWS.values()
     ]


 @router.post("/{name}/trigger")
-def trigger_workflow(name: str, background_tasks: BackgroundTasks):
+def trigger_workflow(
+    name: str,
+    background_tasks: BackgroundTasks,
+    orchestrator: WorkflowOrchestrator = Depends(WorkflowOrchestrator),
+):
     try:
         run_id = orchestrator.trigger_workflow(name, background_tasks)
     except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))
     return {"run_id": run_id}


 @router.get("/runs")
-def list_runs():
-    from app.workflow.repositories import WorkflowRunRepository
-
-    repo = WorkflowRunRepository()
+def list_runs(repo: WorkflowRunRepository = Depends(WorkflowRunRepository)):
     runs = repo.list_all()
     return [run.model_dump() for run in runs]


 @router.get("/runs/{run_id}")
-def get_run(run_id: str):
-    from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository
-
-    run_repo = WorkflowRunRepository()
-    task_repo = WorkflowTaskRunRepository()
-
+def get_run(
+    run_id: str,
+    run_repo: WorkflowRunRepository = Depends(WorkflowRunRepository),
+    task_repo: WorkflowTaskRunRepository = Depends(WorkflowTaskRunRepository),
+):
     try:
         run = run_repo.get(run_id)
     except Exception:
         raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

     task_runs = task_repo.list_by_run(run_id)
     return {
         **run.model_dump(),
         "task_runs": [tr.model_dump() for tr in task_runs],
     }
```

> Note: the `try/except Exception → 404` block above is itself a bug and is fixed separately in **DOA-007** (this task only changes how the repositories are obtained).

## Acceptance criteria

- [ ] `workflow_orchestrator.py` no longer defines a module-level `orchestrator`.
- [ ] `workflow_routes.py` contains no function-level imports and no module-level orchestrator/repository instances.
- [ ] `app.dependency_overrides[WorkflowOrchestrator] = lambda: FakeOrchestrator()` works in a test (verified in DOA-010).
- [ ] All four endpoints smoke-tested green.

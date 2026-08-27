# DOA-006: Orchestrator crash-safety — runs can get stuck in `running` forever; ABC signature is wrong

- **Type:** Bug
- **Priority:** P0
- **Component:** backend / workflow
- **Affected files:** `backend/app/workflow/workflow_orchestrator.py`, `backend/app/workflow/base_workflow_orchestrator.py`

## Problem

1. **Setup code sits outside the `try` block.** In `run_workflow` (`workflow_orchestrator.py:55-59`):

   ```python
   async def run_workflow(self, run_id: str) -> None:
       self.run_repo.update_status(run_id, "running")

       run = self.run_repo.get(run_id)
       config = self.resolve_config(run.workflow_name)

       try:
           ...
   ```

   If `run_repo.get()` raises (transient Supabase error, `.single()` mismatch) or `resolve_config()` raises `ValueError` (workflow removed from the registry after trigger, e.g. across a deploy), the exception escapes `run_workflow` entirely. `BackgroundTasks` just logs it — **the run stays `running` in the DB forever** with no error message. Anything polling `GET /runs/{id}` spins indefinitely.

2. **Exception logging discards the traceback.** `logger.error("Task %s failed: %s", task_name, e)` logs only `str(e)`. For a `KeyError` this can literally log `Task foo failed: 'x'` — undiagnosable. Use `logger.exception(...)` / `exc_info=True`.

3. **The failure handler can itself fail.** In the outer `except`, `update_status(..., "failed", ...)` is another DB call; if the DB is the thing failing, this raises out of the handler and masks the original error. It must be best-effort.

4. **ABC signature mismatch.** `base_workflow_orchestrator.py:19-21` declares `def run_workflow(self, run_id: str) -> None:` (sync), but the concrete implementation is `async def`. Any alternative implementation written against the ABC contract would be wired into `background_tasks.add_task` incorrectly. Declare it `async` in the ABC.

## Steps of completion

1. Move `update_status("running")`, `get(run_id)`, and `resolve_config(...)` inside the `try` block.
2. Switch task/workflow failure logs to `logger.exception(...)` (keeps the traceback).
3. Wrap the outer failure-status write in its own `try/except` so a DB outage can't mask the original exception (log both).
4. Change the ABC's `run_workflow` to `async def`.
5. Test: temporarily register a workflow, trigger it, remove it from `WORKFLOWS`, and force the failure path — the run must end `failed` with a meaningful `error`, never stuck at `running`.

## Changes (diff)

### `backend/app/workflow/base_workflow_orchestrator.py`

```diff
@@ -18,5 +18,5 @@
     @abstractmethod
-    def run_workflow(self, run_id: str) -> None:
+    async def run_workflow(self, run_id: str) -> None:
         ...
```

### `backend/app/workflow/workflow_orchestrator.py`

```diff
@@ -55,33 +55,40 @@
     async def run_workflow(self, run_id: str) -> None:
-        self.run_repo.update_status(run_id, "running")
-
-        run = self.run_repo.get(run_id)
-        config = self.resolve_config(run.workflow_name)
-
         try:
+            self.run_repo.update_status(run_id, "running")
+
+            run = self.run_repo.get(run_id)
+            config = self.resolve_config(run.workflow_name)
+
             for index, task_cls in enumerate(config.tasks):
                 self.run_repo.update_progress(run_id, index)

                 task_run = self.task_run_repo.get(run_id, index)
                 self.task_run_repo.update_running(task_run.id)

                 try:
                     task_instance = task_cls()
                     await task_instance.run()

                     self.task_run_repo.update_status(task_run.id, "completed")
                 except Exception as e:
                     task_name = resolve_task_name(task_cls)
-                    logger.error("Task %s failed: %s", task_name, e)
+                    logger.exception("Task %s in run %s failed", task_name, run_id)
                     self.task_run_repo.update_status(task_run.id, "failed", str(e))
                     self.run_repo.update_status(
                         run_id,
                         "failed",
                         f"Task '{task_name}' failed: {e}",
                     )
                     return

             self.run_repo.update_status(run_id, "completed")
         except Exception as e:
-            logger.error("Workflow %s failed unexpectedly: %s", run_id, e)
-            self.run_repo.update_status(run_id, "failed", f"Unexpected error: {e}")
+            logger.exception("Workflow %s failed unexpectedly", run_id)
+            try:
+                self.run_repo.update_status(run_id, "failed", f"Unexpected error: {e}")
+            except Exception:
+                # Best effort — if even the status write fails, don't mask the
+                # original error; the run may remain 'running' and needs the
+                # startup-recovery sweep (DOA-006 follow-up / DOA-010 test).
+                logger.exception("Failed to mark run %s as failed", run_id)
```

> Note: with this change, a failed `update_status("running")` at the top now routes into the outer handler, which will attempt the `failed` write and log if that also fails — the run can no longer silently escape the state machine while the DB is healthy.

### Optional follow-up (recommended, small): startup recovery of orphaned runs

If the process is killed mid-run (deploy, `--reload`, crash), rows stay `running`. Add a FastAPI startup hook that sweeps them:

```diff
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -1,10 +1,23 @@
+from contextlib import asynccontextmanager
+
 from fastapi import FastAPI
 from fastapi.middleware.cors import CORSMiddleware
 from app.api.v1 import api_router
 from app.core.config import settings
+from app.workflow.repositories import WorkflowRunRepository
+
+
+@asynccontextmanager
+async def lifespan(app: FastAPI):
+    # In-process BackgroundTasks don't survive restarts: anything still
+    # 'running'/'pending' at boot was orphaned by a previous process.
+    WorkflowRunRepository().fail_stale_runs(
+        error="Orphaned by server restart"
+    )
+    yield

 app = FastAPI(
     title=settings.PROJECT_NAME,
+    lifespan=lifespan,
     openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
 )
```

with a matching repository method:

```diff
--- a/backend/app/workflow/repositories/workflow_run_repo.py
+++ b/backend/app/workflow/repositories/workflow_run_repo.py
@@ -30,5 +30,13 @@
     def update_progress(self, run_id: str, current_task_index: int) -> None:
         supabase.table("workflow_runs").update({
             "current_task_index": current_task_index,
             "updated_at": datetime.now(timezone.utc).isoformat(),
         }).eq("id", run_id).execute()
+
+    def fail_stale_runs(self, error: str) -> None:
+        supabase.table("workflow_runs").update({
+            "status": "failed",
+            "error": error,
+            "updated_at": datetime.now(timezone.utc).isoformat(),
+        }).in_("status", ["pending", "running"]).execute()
```

## Acceptance criteria

- [ ] Triggering a workflow whose config disappears (or whose first repo call fails) leaves the run in `failed` with a populated `error`, not `running`.
- [ ] Task failures log full tracebacks.
- [ ] `mypy`/IDE no longer flags the concrete class as incompatible with the ABC.
- [ ] (If startup sweep included) restarting the server while a run is in-flight marks it `failed: Orphaned by server restart`.

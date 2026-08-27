# DOA-005: Stop blocking the event loop — synchronous Supabase calls inside `async run_workflow`

- **Type:** Bug (performance / availability)
- **Priority:** P0
- **Component:** backend / workflow
- **Affected files:** `backend/app/workflow/workflow_orchestrator.py`

## Problem

`WorkflowOrchestrator.run_workflow` (`workflow_orchestrator.py:55-87`) is `async` and is executed by FastAPI's `BackgroundTasks` **on the main event loop**. Every repository call inside it (`update_status`, `get`, `update_progress`, `update_running`) is a **synchronous HTTP round-trip** to Supabase via the sync `supabase-py` client.

Each of those calls blocks the entire event loop for the duration of the network request. While a workflow is running, **every other request to the API stalls** (including `/health`, which defeats liveness probes). With Supabase latency of, say, 100–300 ms and 2 DB writes per task, a 10-task workflow freezes the server for several seconds per run — and indefinitely if Supabase is slow.

## Fix

Wrap every synchronous repository call in `fastapi.concurrency.run_in_threadpool` (Starlette's threadpool offload). This keeps the repositories simple/sync (they're also called from sync route handlers, which FastAPI already runs in a threadpool) while making the async runner loop-safe.

> Coordination note: this task and DOA-006 both rewrite `run_workflow`. Land DOA-006 (error-handling restructure) first, then apply this diff on top — or do both in one PR. The diff below is written against the current `main`.

## Steps of completion

1. Import `run_in_threadpool` in `workflow_orchestrator.py`.
2. Wrap all 6 repository call sites inside `run_workflow` with `await run_in_threadpool(...)`. Do **not** touch `trigger_workflow` — it is called from a sync route handler which FastAPI already offloads.
3. Verify no other `async def` in the backend performs direct repository calls.
4. Manual test: trigger the `sample` workflow (contains a 60 s `DelayTask`) and, while it runs, hit `GET /health` in a loop — responses must stay < 50 ms.

## Before / after

**Before** — `run_workflow` awaits only `task_instance.run()`; all 6 repo calls run inline on the event loop and block it.

**After** — every repo call is offloaded to the threadpool; the event loop stays responsive during workflow execution.

## Changes (diff)

### `backend/app/workflow/workflow_orchestrator.py`

```diff
@@ -3,7 +3,8 @@
 import logging

-from fastapi import BackgroundTasks
+from fastapi import BackgroundTasks
+from fastapi.concurrency import run_in_threadpool

 from app.workflow.base_workflow_orchestrator import BaseWorkflowOrchestrator
@@ -55,33 +56,37 @@
     async def run_workflow(self, run_id: str) -> None:
-        self.run_repo.update_status(run_id, "running")
+        await run_in_threadpool(self.run_repo.update_status, run_id, "running")

-        run = self.run_repo.get(run_id)
+        run = await run_in_threadpool(self.run_repo.get, run_id)
         config = self.resolve_config(run.workflow_name)

         try:
             for index, task_cls in enumerate(config.tasks):
-                self.run_repo.update_progress(run_id, index)
+                await run_in_threadpool(self.run_repo.update_progress, run_id, index)

-                task_run = self.task_run_repo.get(run_id, index)
-                self.task_run_repo.update_running(task_run.id)
+                task_run = await run_in_threadpool(self.task_run_repo.get, run_id, index)
+                await run_in_threadpool(self.task_run_repo.update_running, task_run.id)

                 try:
                     task_instance = task_cls()
                     await task_instance.run()

-                    self.task_run_repo.update_status(task_run.id, "completed")
+                    await run_in_threadpool(
+                        self.task_run_repo.update_status, task_run.id, "completed"
+                    )
                 except Exception as e:
                     task_name = resolve_task_name(task_cls)
                     logger.error("Task %s failed: %s", task_name, e)
-                    self.task_run_repo.update_status(task_run.id, "failed", str(e))
-                    self.run_repo.update_status(
+                    await run_in_threadpool(
+                        self.task_run_repo.update_status, task_run.id, "failed", str(e)
+                    )
+                    await run_in_threadpool(
+                        self.run_repo.update_status,
                         run_id,
                         "failed",
                         f"Task '{task_name}' failed: {e}",
                     )
                     return

-            self.run_repo.update_status(run_id, "completed")
+            await run_in_threadpool(self.run_repo.update_status, run_id, "completed")
         except Exception as e:
             logger.error("Workflow %s failed unexpectedly: %s", run_id, e)
-            self.run_repo.update_status(run_id, "failed", f"Unexpected error: {e}")
+            await run_in_threadpool(
+                self.run_repo.update_status, run_id, "failed", f"Unexpected error: {e}"
+            )
```

*(If DOA-003 has landed, the string literals above are enum members instead — same shape.)*

## Acceptance criteria

- [ ] No bare `self.run_repo.*` / `self.task_run_repo.*` calls remain inside `async def run_workflow`.
- [ ] `/health` latency stays flat while a `sample` workflow (60 s delay) is running.
- [ ] Workflow still transitions `pending → running → completed` and task rows get `started_at`/`completed_at`.

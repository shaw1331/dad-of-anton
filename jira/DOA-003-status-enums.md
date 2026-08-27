# DOA-003: Replace free-string workflow/task statuses with enums

- **Type:** Tech debt / Correctness hardening
- **Priority:** P1
- **Component:** backend / workflow
- **Affected files:** new `backend/app/workflow/models/status.py`, `backend/app/workflow/models/workflow_run.py`, `backend/app/workflow/models/workflow_task_run.py`, `backend/app/workflow/workflow_orchestrator.py`, `backend/app/workflow/repositories/workflow_run_repo.py`, `backend/app/workflow/repositories/workflow_task_run_repo.py`, `backend/app/workflow/models/__init__.py`

## Problem

Statuses are magic strings scattered across five files: `"pending"` (orchestrator lines 36, 47), `"running"` (orchestrator line 56, task repo line 41), `"completed"` (orchestrator lines 72, 84), `"failed"` (orchestrator lines 76, 78, 87). A typo like `"complete"` would be accepted silently by Pydantic (`status: str`), stored in the DB, and break any consumer filtering on status. There is no single source of truth for the state machine.

## Fix

Introduce `WorkflowStatus` and `TaskStatus` as `str`-based enums, type the models with them, and use enum members everywhere. Because they subclass `str`, JSON serialization and Supabase inserts keep working unchanged; Pydantic will now *reject* unknown status strings coming back from the DB.

## Steps of completion

1. Create `backend/app/workflow/models/status.py` with the two enums.
2. Export them from `backend/app/workflow/models/__init__.py`.
3. Change `status: str` → `status: WorkflowStatus` / `status: TaskStatus` in the two models.
4. Replace every string literal in the orchestrator with enum members.
5. Type the repository `update_status` signatures with the enums and pass `status.value` into the update payloads (explicit, and independent of client JSON encoders).
6. Trigger the sample workflow and confirm rows in Supabase still contain the same lowercase strings as before (no data-format change).

## Changes (diff)

### `backend/app/workflow/models/status.py` (new file)

```diff
@@ -0,0 +1,17 @@
+from __future__ import annotations
+
+from enum import Enum
+
+
+class WorkflowStatus(str, Enum):
+    PENDING = "pending"
+    RUNNING = "running"
+    COMPLETED = "completed"
+    FAILED = "failed"
+
+
+class TaskStatus(str, Enum):
+    PENDING = "pending"
+    RUNNING = "running"
+    COMPLETED = "completed"
+    FAILED = "failed"
```

### `backend/app/workflow/models/__init__.py`

```diff
+from app.workflow.models.status import TaskStatus, WorkflowStatus
 from app.workflow.models.workflow_run import WorkflowRun
 from app.workflow.models.workflow_task_run import WorkflowTaskRun

-__all__ = ["WorkflowRun", "WorkflowTaskRun"]
+__all__ = ["TaskStatus", "WorkflowRun", "WorkflowStatus", "WorkflowTaskRun"]
```

*(adjust to the file's existing export style if it differs)*

### `backend/app/workflow/models/workflow_run.py`

```diff
@@ -1,11 +1,12 @@
 from __future__ import annotations

 from app.models.base import BaseModel
+from app.workflow.models.status import WorkflowStatus


 class WorkflowRun(BaseModel):
     workflow_name: str
-    status: str
+    status: WorkflowStatus
     current_task_index: int
     total_tasks: int
     error: str | None = None
```

### `backend/app/workflow/models/workflow_task_run.py`

```diff
@@ -1,13 +1,14 @@
 from __future__ import annotations

 from app.models.base import BaseModel
+from app.workflow.models.status import TaskStatus


 class WorkflowTaskRun(BaseModel):
     workflow_run_id: str
     task_name: str
     task_index: int
-    status: str
+    status: TaskStatus
     error: str | None = None
     started_at: str | None = None
     completed_at: str | None = None
```

### `backend/app/workflow/workflow_orchestrator.py`

```diff
@@ -6,8 +6,8 @@
 from fastapi import BackgroundTasks

 from app.workflow.base_workflow_orchestrator import BaseWorkflowOrchestrator
-from app.workflow.models import WorkflowRun, WorkflowTaskRun
+from app.workflow.models import TaskStatus, WorkflowRun, WorkflowStatus, WorkflowTaskRun
 from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository
@@ -33,7 +33,7 @@
         run = WorkflowRun(
             workflow_name=workflow_name,
-            status="pending",
+            status=WorkflowStatus.PENDING,
             current_task_index=0,
             total_tasks=len(config.tasks),
         )
@@ -44,7 +44,7 @@
             task_run = WorkflowTaskRun(
                 workflow_run_id=run.id,
                 task_name=resolve_task_name(task_cls),
                 task_index=index,
-                status="pending",
+                status=TaskStatus.PENDING,
             )
@@ -55,7 +55,7 @@
     async def run_workflow(self, run_id: str) -> None:
-        self.run_repo.update_status(run_id, "running")
+        self.run_repo.update_status(run_id, WorkflowStatus.RUNNING)
@@ -70,18 +70,18 @@
                     task_instance = task_cls()
                     await task_instance.run()

-                    self.task_run_repo.update_status(task_run.id, "completed")
+                    self.task_run_repo.update_status(task_run.id, TaskStatus.COMPLETED)
                 except Exception as e:
                     task_name = resolve_task_name(task_cls)
                     logger.error("Task %s failed: %s", task_name, e)
-                    self.task_run_repo.update_status(task_run.id, "failed", str(e))
+                    self.task_run_repo.update_status(task_run.id, TaskStatus.FAILED, str(e))
                     self.run_repo.update_status(
                         run_id,
-                        "failed",
+                        WorkflowStatus.FAILED,
                         f"Task '{task_name}' failed: {e}",
                     )
                     return

-            self.run_repo.update_status(run_id, "completed")
+            self.run_repo.update_status(run_id, WorkflowStatus.COMPLETED)
         except Exception as e:
             logger.error("Workflow %s failed unexpectedly: %s", run_id, e)
-            self.run_repo.update_status(run_id, "failed", f"Unexpected error: {e}")
+            self.run_repo.update_status(run_id, WorkflowStatus.FAILED, f"Unexpected error: {e}")
```

### `backend/app/workflow/repositories/workflow_run_repo.py`

```diff
@@ -5,6 +5,7 @@
 from app.core.database import supabase
 from app.workflow.models.workflow_run import WorkflowRun
+from app.workflow.models.status import WorkflowStatus
@@ -17,9 +18,9 @@
-    def update_status(self, run_id: str, status: str, error: str | None = None) -> None:
+    def update_status(self, run_id: str, status: WorkflowStatus, error: str | None = None) -> None:
         data: dict = {
-            "status": status,
+            "status": status.value,
             "updated_at": datetime.now(timezone.utc).isoformat(),
         }
```

### `backend/app/workflow/repositories/workflow_task_run_repo.py`

```diff
@@ -5,6 +5,7 @@
 from app.core.database import supabase
 from app.workflow.models.workflow_task_run import WorkflowTaskRun
+from app.workflow.models.status import TaskStatus
@@ -30,9 +31,9 @@
-    def update_status(self, task_run_id: str, status: str, error: str | None = None) -> None:
+    def update_status(self, task_run_id: str, status: TaskStatus, error: str | None = None) -> None:
         data: dict = {
-            "status": status,
+            "status": status.value,
             "completed_at": datetime.now(timezone.utc).isoformat(),
         }
@@ -39,7 +40,7 @@
     def update_running(self, task_run_id: str) -> None:
         supabase.table("workflow_task_runs").update({
-            "status": "running",
+            "status": TaskStatus.RUNNING.value,
             "started_at": datetime.now(timezone.utc).isoformat(),
         }).eq("id", task_run_id).execute()
```

> Optional follow-up: add a `CHECK (status IN ('pending','running','completed','failed'))` constraint migration so the DB enforces the same contract.

## Acceptance criteria

- [ ] `grep -rn '"pending"\|"running"\|"completed"\|"failed"' backend/app/workflow --include='*.py'` returns only `status.py`.
- [ ] Rows written to Supabase are byte-identical to before (lowercase strings).
- [ ] Loading a row with an unknown status raises a Pydantic `ValidationError` (add a unit test in DOA-010).

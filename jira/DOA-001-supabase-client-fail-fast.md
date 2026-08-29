# DOA-001: Fail fast when Supabase is not configured (fix `None`-client crash)

- **Type:** Bug
- **Priority:** P0
- **Component:** backend / core
- **Affected files:** `backend/app/core/database.py`, `backend/app/workflow/repositories/workflow_run_repo.py`, `backend/app/workflow/repositories/workflow_task_run_repo.py`

## Problem

`backend/app/core/database.py` declares the client as optional and silently leaves it as `None` when env vars are missing:

```python
supabase: Client | None = None

if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
```

Both repositories import that module-level name and call it unconditionally, e.g. `workflow_run_repo.py:11`:

```python
supabase.table("workflow_runs").insert(run.model_dump(mode="json")).execute()
```

If `SUPABASE_URL` / `SUPABASE_ANON_KEY` are unset, the app **starts up fine** and then every request or background workflow dies deep in a repository with:

```
AttributeError: 'NoneType' object has no attribute 'table'
```

Worse, in `run_workflow` (a background task) this exception is swallowed into a generic "failed" status — or, if the failure happens in `update_status` itself, is lost entirely. The failure surface is far from the root cause (missing config).

## Fix

Replace the optional module-level client with a lazy accessor `get_supabase()` that raises a clear `RuntimeError` naming the missing env vars. Repositories call the accessor instead of importing a possibly-`None` global.

## Steps of completion

1. Rewrite `backend/app/core/database.py` to expose `get_supabase() -> Client` (lazy singleton, clear error message).
2. Update both repositories to import `get_supabase` and call it in every method.
3. Boot the backend **without** a `.env` and hit `GET /api/v1/workflows/runs` — verify the response is a 500 whose log clearly says Supabase is unconfigured (instead of a `NoneType` AttributeError).
4. Boot with a valid `.env` and verify `trigger` / `runs` / `runs/{id}` endpoints still work end-to-end.

## Before / after

**Before** — `backend/app/core/database.py` (entire file, 9 lines): client may be `None`; every caller assumes it is not.

**After** — a `get_supabase()` accessor that either returns a real `Client` or raises immediately with an actionable message; the client is created once and cached.

## Changes (diff)

### `backend/app/core/database.py`

```diff
@@ -1,9 +1,22 @@
 from __future__ import annotations

 from supabase import create_client, Client
 from app.core.config import settings

-supabase: Client | None = None
-
-if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
-    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
+_client: Client | None = None
+
+
+def get_supabase() -> Client:
+    """Return the shared Supabase client, creating it on first use.
+
+    Raises RuntimeError when credentials are missing so callers fail with an
+    actionable message instead of `'NoneType' object has no attribute 'table'`.
+    """
+    global _client
+    if _client is None:
+        if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
+            raise RuntimeError(
+                "Supabase is not configured: set SUPABASE_URL and "
+                "SUPABASE_ANON_KEY in backend/.env"
+            )
+        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
+    return _client
```

### `backend/app/workflow/repositories/workflow_run_repo.py`

```diff
@@ -1,10 +1,10 @@
 from __future__ import annotations

 from datetime import datetime, timezone

-from app.core.database import supabase
+from app.core.database import get_supabase
 from app.workflow.models.workflow_run import WorkflowRun


 class WorkflowRunRepository:
     def create(self, run: WorkflowRun) -> None:
-        supabase.table("workflow_runs").insert(run.model_dump(mode="json")).execute()
+        get_supabase().table("workflow_runs").insert(run.model_dump(mode="json")).execute()

     def get(self, run_id: str) -> WorkflowRun:
-        result = supabase.table("workflow_runs").select("*").eq("id", run_id).single().execute()
+        result = get_supabase().table("workflow_runs").select("*").eq("id", run_id).single().execute()
         return WorkflowRun.model_validate(result.data)

     def update_status(self, run_id: str, status: str, error: str | None = None) -> None:
         data: dict = {
             "status": status,
             "updated_at": datetime.now(timezone.utc).isoformat(),
         }
         if error is not None:
             data["error"] = error
-        supabase.table("workflow_runs").update(data).eq("id", run_id).execute()
+        get_supabase().table("workflow_runs").update(data).eq("id", run_id).execute()

     def list_all(self) -> list[WorkflowRun]:
-        result = supabase.table("workflow_runs").select("*").order("created_at", desc=True).execute()
+        result = get_supabase().table("workflow_runs").select("*").order("created_at", desc=True).execute()
         return [WorkflowRun.model_validate(row) for row in result.data]

     def update_progress(self, run_id: str, current_task_index: int) -> None:
-        supabase.table("workflow_runs").update({
+        get_supabase().table("workflow_runs").update({
             "current_task_index": current_task_index,
             "updated_at": datetime.now(timezone.utc).isoformat(),
         }).eq("id", run_id).execute()
```

### `backend/app/workflow/repositories/workflow_task_run_repo.py`

```diff
@@ -1,10 +1,10 @@
 from __future__ import annotations

 from datetime import datetime, timezone

-from app.core.database import supabase
+from app.core.database import get_supabase
 from app.workflow.models.workflow_task_run import WorkflowTaskRun


 class WorkflowTaskRunRepository:
     def create(self, task_run: WorkflowTaskRun) -> None:
-        supabase.table("workflow_task_runs").insert(task_run.model_dump(mode="json")).execute()
+        get_supabase().table("workflow_task_runs").insert(task_run.model_dump(mode="json")).execute()

     def get(self, workflow_run_id: str, task_index: int) -> WorkflowTaskRun:
-        result = supabase.table("workflow_task_runs") \
+        result = get_supabase().table("workflow_task_runs") \
             .select("*") \
             .eq("workflow_run_id", workflow_run_id) \
             .eq("task_index", task_index) \
             .single() \
             .execute()
         return WorkflowTaskRun.model_validate(result.data)

     def list_by_run(self, workflow_run_id: str) -> list[WorkflowTaskRun]:
-        result = supabase.table("workflow_task_runs") \
+        result = get_supabase().table("workflow_task_runs") \
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
-        supabase.table("workflow_task_runs").update(data).eq("id", task_run_id).execute()
+        get_supabase().table("workflow_task_runs").update(data).eq("id", task_run_id).execute()

     def update_running(self, task_run_id: str) -> None:
-        supabase.table("workflow_task_runs").update({
+        get_supabase().table("workflow_task_runs").update({
             "status": "running",
             "started_at": datetime.now(timezone.utc).isoformat(),
         }).eq("id", task_run_id).execute()
```

## Acceptance criteria

- [ ] Backend with missing env vars fails with `RuntimeError: Supabase is not configured...` on first DB access (clear log line, not `AttributeError`).
- [ ] No module in the codebase imports the removed `supabase` global (`grep -r "from app.core.database import supabase"` returns nothing).
- [ ] All workflow endpoints behave unchanged with valid credentials.

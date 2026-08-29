# DOA-007: API hygiene — bare-except 404 masking, unbounded `/runs`, duplicate health endpoints

- **Type:** Bug / Tech debt
- **Priority:** P1
- **Component:** backend / api
- **Affected files:** `backend/app/api/v1/workflow_routes.py`, `backend/app/workflow/repositories/workflow_run_repo.py`, `backend/app/api/v1/__init__.py`
- **Depends on:** DOA-002 (routes refactored to `Depends`) — diffs below assume DOA-002 has landed; apply the same logic to the current code if sequenced differently.

## Problems

1. **`except Exception → 404` masks real failures.** `workflow_routes.py:46-49`:

   ```python
   try:
       run = run_repo.get(run_id)
   except Exception:
       raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
   ```

   A Supabase outage, auth failure, or the DOA-001 misconfiguration error all come back to the client as **404 Run not found** — actively misleading during incidents. Only "zero rows" should map to 404.

2. **`GET /runs` is unbounded.** `list_all()` selects every row ever created, ordered desc. Grows without limit; no `limit`/`offset` parameters.

3. **Duplicate health endpoints.** `main.py:22-24` exposes `GET /health` and `api/v1/__init__.py:10-12` exposes `GET /api/v1/health` with slightly different payloads. Keep the root one for infra probes; drop the v1 duplicate. (Frontend fetch is updated in DOA-008.)

## Fix

- Add `get_or_none(run_id)` to the run repository using `maybe_single()` (returns `None` on zero rows instead of raising), and let unexpected exceptions propagate as 500s.
- Add `limit`/`offset` query params to `GET /runs` backed by Supabase `.range()`.
- Delete the `/api/v1/health` duplicate.

## Steps of completion

1. Add `get_or_none` and `list_page` methods to `WorkflowRunRepository` (keep `get`/`list_all` for internal orchestrator use, or migrate callers and delete — reviewer's choice; diff keeps both).
2. Rewrite `get_run` to branch on `None` → 404; remove the `try/except`.
3. Add `limit: int = Query(50, ge=1, le=200)` and `offset: int = Query(0, ge=0)` to `list_runs`.
4. Remove the health route from `api/v1/__init__.py`.
5. Smoke-test: unknown id → 404; misconfigured Supabase → 500 (not 404); `GET /runs?limit=2&offset=2` pages correctly.

## Changes (diff)

### `backend/app/workflow/repositories/workflow_run_repo.py`

```diff
@@ -13,6 +13,14 @@
     def get(self, run_id: str) -> WorkflowRun:
         result = supabase.table("workflow_runs").select("*").eq("id", run_id).single().execute()
         return WorkflowRun.model_validate(result.data)

+    def get_or_none(self, run_id: str) -> WorkflowRun | None:
+        result = (
+            supabase.table("workflow_runs")
+            .select("*").eq("id", run_id).maybe_single().execute()
+        )
+        if result is None or result.data is None:
+            return None
+        return WorkflowRun.model_validate(result.data)
+
@@ -26,5 +34,14 @@
     def list_all(self) -> list[WorkflowRun]:
         result = supabase.table("workflow_runs").select("*").order("created_at", desc=True).execute()
         return [WorkflowRun.model_validate(row) for row in result.data]

+    def list_page(self, limit: int, offset: int) -> list[WorkflowRun]:
+        result = (
+            supabase.table("workflow_runs")
+            .select("*")
+            .order("created_at", desc=True)
+            .range(offset, offset + limit - 1)
+            .execute()
+        )
+        return [WorkflowRun.model_validate(row) for row in result.data]
```

### `backend/app/api/v1/workflow_routes.py`

```diff
@@ -1,8 +1,8 @@
 from __future__ import annotations

-from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
+from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
@@ -30,8 +30,12 @@
 @router.get("/runs")
-def list_runs(repo: WorkflowRunRepository = Depends(WorkflowRunRepository)):
-    runs = repo.list_all()
+def list_runs(
+    limit: int = Query(50, ge=1, le=200),
+    offset: int = Query(0, ge=0),
+    repo: WorkflowRunRepository = Depends(WorkflowRunRepository),
+):
+    runs = repo.list_page(limit=limit, offset=offset)
     return [run.model_dump() for run in runs]


 @router.get("/runs/{run_id}")
 def get_run(
     run_id: str,
     run_repo: WorkflowRunRepository = Depends(WorkflowRunRepository),
     task_repo: WorkflowTaskRunRepository = Depends(WorkflowTaskRunRepository),
 ):
-    try:
-        run = run_repo.get(run_id)
-    except Exception:
+    run = run_repo.get_or_none(run_id)
+    if run is None:
         raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

     task_runs = task_repo.list_by_run(run_id)
     return {
         **run.model_dump(),
         "task_runs": [tr.model_dump() for tr in task_runs],
     }
```

### `backend/app/api/v1/__init__.py`

```diff
@@ -1,12 +1,7 @@
 from fastapi import APIRouter

 from app.api.v1.workflow_routes import router as workflow_router

 api_router = APIRouter()

 api_router.include_router(workflow_router)
-
-
-@api_router.get("/health")
-def health_check():
-    return {"status": "healthy", "service": "dad-of-anton-api"}
```

> ⚠️ The frontend `HealthCheck.tsx` currently calls `/api/v1/health`. Land **DOA-008** (which repoints it to `/health`) in the same release, or keep the v1 route until DOA-008 ships.

## Acceptance criteria

- [ ] `GET /api/v1/workflows/runs/<random-uuid>` → 404; with Supabase down/misconfigured → 500.
- [ ] `GET /api/v1/workflows/runs?limit=1` returns exactly 1 row; `offset` shifts the window.
- [ ] Exactly one health endpoint remains (`GET /health`), and the frontend still shows backend health after DOA-008.

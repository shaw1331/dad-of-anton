# DOA-010: Add a backend test suite (pytest) — orchestrator + routes

- **Type:** Task (test coverage)
- **Priority:** P1
- **Component:** backend / tests
- **Affected files:** new `backend/requirements-dev.txt`, new `backend/tests/__init__.py`, new `backend/tests/test_orchestrator.py`, new `backend/tests/test_workflow_routes.py`
- **Depends on:** DOA-002 (dependency injection makes route tests possible without a live Supabase)

## Problem

The backend has **zero tests**. The orchestrator's state machine (pending → running → completed/failed), its failure paths, and the API contract are all unverified; every refactor in this epic (DOA-001…009) is currently landing blind. The org gate requires ≥60% new-code coverage before PR.

## Fix

Add pytest with in-memory fake repositories (no Supabase dependency) covering:

- happy path: all tasks complete, statuses recorded in order;
- failing task: task marked `failed` with error, run marked `failed`, later tasks never run;
- unknown workflow name: `trigger_workflow` raises `ValueError`; route returns 404;
- route contract: `GET /workflows` lists registry entries; `GET /runs/{id}` 404s on missing id.

## Steps of completion

1. Create `backend/requirements-dev.txt` (pinned) and install into the venv.
2. Create the `tests/` package with the fakes and the four test modules' contents below.
3. Run `cd backend && python -m pytest tests/ -v` — all green.
4. Wire into CI if/when a pipeline exists (out of scope here).

## Changes (diff)

### `backend/requirements-dev.txt` (new file)

```diff
@@ -0,0 +1,4 @@
+pytest==8.3.4
+pytest-asyncio==0.25.0
+httpx==0.28.1
+anyio==4.7.0
```

### `backend/tests/__init__.py` (new file)

```diff
@@ -0,0 +1 @@
+
```

### `backend/tests/test_orchestrator.py` (new file)

```diff
@@ -0,0 +1,120 @@
+from __future__ import annotations
+
+import pytest
+
+from app.workflow.models import WorkflowRun, WorkflowTaskRun
+from app.workflow.workflow_config import BaseWorkflowConfig
+from app.workflow.workflow_orchestrator import WorkflowOrchestrator
+from app.workflow.workflow_registry import WORKFLOWS
+from app.workflow.workflow_task import BaseWorkflowTask
+
+
+class FakeRunRepo:
+    def __init__(self) -> None:
+        self.runs: dict[str, WorkflowRun] = {}
+
+    def create(self, run: WorkflowRun) -> None:
+        self.runs[run.id] = run
+
+    def get(self, run_id: str) -> WorkflowRun:
+        return self.runs[run_id]
+
+    def update_status(self, run_id, status, error=None) -> None:
+        run = self.runs[run_id]
+        self.runs[run_id] = run.model_copy(update={"status": status, "error": error or run.error})
+
+    def update_progress(self, run_id, current_task_index) -> None:
+        run = self.runs[run_id]
+        self.runs[run_id] = run.model_copy(update={"current_task_index": current_task_index})
+
+
+class FakeTaskRunRepo:
+    def __init__(self) -> None:
+        self.task_runs: dict[str, WorkflowTaskRun] = {}
+
+    def create(self, task_run: WorkflowTaskRun) -> None:
+        self.task_runs[task_run.id] = task_run
+
+    def get(self, workflow_run_id, task_index) -> WorkflowTaskRun:
+        return next(
+            tr for tr in self.task_runs.values()
+            if tr.workflow_run_id == workflow_run_id and tr.task_index == task_index
+        )
+
+    def update_status(self, task_run_id, status, error=None) -> None:
+        tr = self.task_runs[task_run_id]
+        self.task_runs[task_run_id] = tr.model_copy(update={"status": status, "error": error or tr.error})
+
+    def update_running(self, task_run_id) -> None:
+        self.update_status(task_run_id, "running")
+
+
+class OkTask(BaseWorkflowTask):
+    name = "ok"
+
+    async def run(self) -> None:
+        pass
+
+
+class BoomTask(BaseWorkflowTask):
+    name = "boom"
+
+    async def run(self) -> None:
+        raise RuntimeError("boom")
+
+
+class DummyBackgroundTasks:
+    def __init__(self) -> None:
+        self.calls = []
+
+    def add_task(self, fn, *args, **kwargs) -> None:
+        self.calls.append((fn, args, kwargs))
+
+
+@pytest.fixture()
+def orchestrator():
+    orch = WorkflowOrchestrator()
+    orch.run_repo = FakeRunRepo()
+    orch.task_run_repo = FakeTaskRunRepo()
+    return orch
+
+
+@pytest.fixture(autouse=True)
+def registry():
+    saved = dict(WORKFLOWS)
+    WORKFLOWS.clear()
+    WORKFLOWS["ok_flow"] = BaseWorkflowConfig("ok_flow", "two ok tasks", [OkTask, OkTask])
+    WORKFLOWS["boom_flow"] = BaseWorkflowConfig("boom_flow", "fails mid-run", [OkTask, BoomTask, OkTask])
+    yield
+    WORKFLOWS.clear()
+    WORKFLOWS.update(saved)
+
+
+def test_trigger_unknown_workflow_raises(orchestrator):
+    with pytest.raises(ValueError):
+        orchestrator.trigger_workflow("nope", DummyBackgroundTasks())
+
+
+def test_trigger_creates_run_and_pending_tasks(orchestrator):
+    bg = DummyBackgroundTasks()
+    run_id = orchestrator.trigger_workflow("ok_flow", bg)
+    assert orchestrator.run_repo.runs[run_id].status == "pending"
+    assert len(orchestrator.task_run_repo.task_runs) == 2
+    assert len(bg.calls) == 1
+
+
+@pytest.mark.asyncio
+async def test_run_workflow_happy_path(orchestrator):
+    run_id = orchestrator.trigger_workflow("ok_flow", DummyBackgroundTasks())
+    await orchestrator.run_workflow(run_id)
+    assert orchestrator.run_repo.runs[run_id].status == "completed"
+    assert all(tr.status == "completed" for tr in orchestrator.task_run_repo.task_runs.values())
+
+
+@pytest.mark.asyncio
+async def test_run_workflow_task_failure_stops_run(orchestrator):
+    run_id = orchestrator.trigger_workflow("boom_flow", DummyBackgroundTasks())
+    await orchestrator.run_workflow(run_id)
+    run = orchestrator.run_repo.runs[run_id]
+    assert run.status == "failed"
+    assert "boom" in (run.error or "")
+    statuses = {tr.task_index: tr.status for tr in orchestrator.task_run_repo.task_runs.values()}
+    assert statuses[0] == "completed"
+    assert statuses[1] == "failed"
+    assert statuses[2] == "pending"  # never started
```

### `backend/tests/test_workflow_routes.py` (new file)

```diff
@@ -0,0 +1,45 @@
+from __future__ import annotations
+
+from fastapi.testclient import TestClient
+
+from app.main import app
+from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository
+
+from tests.test_orchestrator import FakeRunRepo, FakeTaskRunRepo
+
+
+def make_client(run_repo=None, task_repo=None) -> TestClient:
+    app.dependency_overrides[WorkflowRunRepository] = lambda: run_repo or FakeRunRepo()
+    app.dependency_overrides[WorkflowTaskRunRepository] = lambda: task_repo or FakeTaskRunRepo()
+    return TestClient(app)
+
+
+def teardown_module() -> None:
+    app.dependency_overrides.clear()
+
+
+def test_health():
+    client = make_client()
+    assert client.get("/health").json() == {"status": "healthy"}
+
+
+def test_list_workflows_contains_registry_entries():
+    client = make_client()
+    body = client.get("/api/v1/workflows").json()
+    assert isinstance(body, list)
+    for item in body:
+        assert {"name", "description", "task_count"} <= item.keys()
+
+
+def test_trigger_unknown_workflow_is_404():
+    client = make_client()
+    resp = client.post("/api/v1/workflows/does-not-exist/trigger")
+    assert resp.status_code == 404
+
+
+def test_get_missing_run_is_404():
+    client = make_client()
+    resp = client.get("/api/v1/workflows/runs/00000000-0000-0000-0000-000000000000")
+    assert resp.status_code == 404
```

> `test_get_missing_run_is_404` assumes DOA-007's `get_or_none` on the repository (add `get_or_none` returning `None` to `FakeRunRepo` when DOA-007 lands: `def get_or_none(self, run_id): return self.runs.get(run_id)`). The fakes also assume string statuses; after DOA-003, compare against the enum values.
> Note: `test_trigger_unknown_workflow_is_404` exercises the orchestrator through `Depends(WorkflowOrchestrator)`; because `resolve_config` only touches the in-process registry, it needs no DB. Tests that would trigger a *real* workflow through HTTP are intentionally omitted — the orchestrator builds its own repos in `__init__`; injecting them is covered by the unit tests above.

## Acceptance criteria

- [ ] `cd backend && python -m pytest tests/ -v` passes with no Supabase credentials configured.
- [ ] Coverage of `app/workflow/workflow_orchestrator.py` ≥ 60% (org Sonar gate).
- [ ] Tests do not hit the network (fail if `SUPABASE_URL` unset proves nothing leaked).

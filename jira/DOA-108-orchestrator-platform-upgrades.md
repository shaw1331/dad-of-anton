# DOA-108: Orchestrator platform upgrades ASIL needs — data passing, scheduling, retries, fan-out

- **Type:** Task (platform)
- **Priority:** P0 within epic DOA-100 (data passing: M1; scheduling: M2; fan-out: M2-optional)
- **Component:** backend/workflow
- **Depends on:** DOA-005 (non-blocking), DOA-006 (crash safety), DOA-014 (task instances) — hard prerequisites

## Problem

The orchestrator runs a fixed list of `run()`-no-args tasks with no way to (1) pass data between tasks, (2) run on a schedule, (3) retry a flaky task, or (4) execute independent work in parallel. ASIL needs 1–2 for M1/M2 and benefits from 3–4. Each capability below is decided separately with approaches and pros/cons.

---

## Capability 1 — Inter-task data passing (M1, required)

`GenerateCandidatesTask` must hand candidate hashes to `EvaluateBatchTask`, etc.

**A. Shared mutable context dict** — orchestrator creates `ctx = {}` per run, passes to `task.run(ctx)`.
- ✅ Simplest possible; in-memory, zero schema.
- ❌ Invisible to observability (what was in ctx when it crashed?); lost on failure — reruns can't resume; encourages unstructured coupling between tasks (stringly-typed keys).

**B. DB-mediated state: tasks read/write domain tables keyed by a run-scoped id** — *recommended*
Each ASIL task reads its input from DOA-109 tables filtered by `generation_id` and writes its output there; orchestrator only passes the id.
- ✅ Crash-resumable and auditable by construction (the data *is* the state); zero orchestrator changes beyond DOA-014 (the id arrives via task constructor params or a single `run(run_id)` arg).
- ✅ Tasks are independently testable against fixtures.
- ❌ Every pipeline must design its tables (right cost, in our view); slower than memory (irrelevant at our scale).

**C. Orchestrator-persisted task outputs** (a `task_outputs` JSONB column; each task's return value stored, next task receives predecessor outputs).
- ✅ Generic: any future workflow gets data passing for free; great observability.
- ❌ Real design surface (size limits, serialization contract, partial-failure semantics) — building generic workflow-engine features for one consumer is how in-house orchestrators die; JSONB blobs of candidate lists duplicate what DOA-109 stores properly anyway.

**Decision:** **B** for ASIL; add a `run(run_id: str)` context argument to `BaseWorkflowTask.run()` signature (small, generic, non-committal). Revisit C only when a *second* pipeline needs passing.

```diff
--- a/backend/app/workflow/workflow_task.py
+++ b/backend/app/workflow/workflow_task.py
     @abstractmethod
-    async def run(self) -> None:
+    async def run(self, run_id: str) -> None:
         pass
```
*(orchestrator call site: `await task.run(run_id)`; sample tasks take `**_`-style ignore or the arg.)*

---

## Capability 2 — Scheduling (M2, required)

**A. External cron / GitHub Actions hitting the trigger endpoint.**
- ✅ Zero backend code; pause = disable cron.
- ❌ Truth split across systems; needs an exposed endpoint + auth (currently none — see DOA-111); the repo's dev machine (a laptop, per `run.bat`/Downloads path) makes external cron pointing at localhost fragile.

**B. In-process scheduler: asyncio ticker in FastAPI lifespan checking a `schedules` table — *recommended*.**
Table: `(workflow_name, cron_expr or interval, enabled, last_triggered_at)`; a background asyncio task wakes every 60 s, triggers due workflows via the orchestrator directly (no HTTP).
- ✅ One source of truth, visible in the UI (DOA-110 can toggle `enabled`); no exposed endpoints; ~80 lines with `croniter` (pinned).
- ✅ Overlap guard (DOA-106) composes naturally — scheduler skips if previous run still `running`, logging the skip.
- ❌ Only runs while the server runs (acceptable: the whole system is in-process anyway — documented limitation); a second uvicorn worker would double-fire (guard: advisory lock via a `pg_try_advisory_lock`-style claim column, or document single-worker deployment — v1 does the latter, enforced in start.sh `--workers 1`).

**C. APScheduler dependency.**
- ✅ Mature cron semantics, jitter, misfire policies off the shelf.
- ❌ Another framework with its own job store/threading model overlapping our orchestrator's; still needs the same single-worker discipline; heavier than the 80 lines it replaces.

**Decision:** **B**, with A as the interim until it lands.

---

## Capability 3 — Per-task retries (M2, nice-to-have)

**A. Orchestrator-level retry policy** (`max_retries`, `backoff` per task instance; on exception re-run task, `attempt` column on `workflow_task_runs`).
- ✅ Generic; converts flaky-network task failures (price ingest!) from failed generations into hiccups; small (retry loop around the existing try/except in `run_workflow`).
- ❌ Requires task idempotency discipline (document on `BaseWorkflowTask`; ASIL tasks already idempotent by hash/PK design).

**B. In-task retries** (each task handles its own).
- ✅ No platform change; task knows what's retryable.
- ❌ Copy-pasted retry code in every task; invisible in `workflow_task_runs`.

**Decision:** **A**, default `max_retries=0` (opt-in per task instance) — ingest tasks set 2, evaluation tasks 0 (deterministic code shouldn't flake; a retry there hides bugs).

---

## Capability 4 — Parallel fan-out within a task position (M2, optional)

Evaluate 100 candidates concurrently instead of sequentially.

**A. Don't.** DOA-104 targets <1 s/eval ⇒ ~100 s/generation sequential. ✅ Zero work/risk. ❌ Caps future budget growth.
**B. `asyncio.gather` inside `EvaluateBatchTask`** with a semaphore (evals are CPU-bound pandas → actually needs `run_in_threadpool` chunks; GIL limits gains to I/O overlap).
**C. First-class orchestrator parallel stages** (task groups). Generic but a big engine change for one consumer.

**Decision:** **A for launch**, measure, then **B** if generation wall-clock exceeds its 30-min budget; C is explicitly rejected for now.

## Steps of completion

1. `run(run_id)` signature change + orchestrator call site + sample workflow update (coordinate with DOA-014; one PR).
2. `schedules` migration + lifespan ticker + `croniter` pin + single-worker note in start.sh/README.
3. Retry policy fields on task instances + attempt tracking migration (`ALTER TABLE workflow_task_runs ADD COLUMN attempt int NOT NULL DEFAULT 0`) + tests (task failing twice then succeeding → run completes, 3 task_run attempts recorded).
4. Docs: idempotency contract on `BaseWorkflowTask` docstring.

## Acceptance criteria

- [ ] A task can read its predecessor's output via DB using only `run_id` (demonstrated by the M1 `scrape_import` → stats task pair).
- [ ] A schedule row `enabled=true, interval='0 2 * * *'` triggers the workflow at 02:00 and skips when the prior run is still running (logged).
- [ ] Ingest task with `max_retries=2` survives two injected failures; evaluation task with 0 fails fast.
- [ ] Existing sample workflow and all DOA-010 tests still pass after the signature change.

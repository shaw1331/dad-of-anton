# DOA-106: The improvement loop controller — generations, selection, budgets, stopping

- **Type:** Task (core loop stage)
- **Priority:** P0 within epic DOA-100 (M2)
- **Component:** backend/workflow
- **Depends on:** DOA-104 (evaluate), DOA-105 (generate), DOA-107 (gates), DOA-108 (scheduling + data passing), DOA-109 (state)

## Problem

Something has to *be* the loop: decide when a generation runs, hold the budget, call generate → evaluate → gate → select in order, persist population state between generations, and stop when continuing is waste. This ticket is the controller; per DOA-100 §7 the epic already chose **one workflow run per generation (Option B)** — this ticket decides how the controller is structured *within* that shape.

## Approaches

### A. Controller as a workflow definition on the existing orchestrator — *recommended*
A registered `asil_generation` workflow: `[LoadPopulationTask, GenerateCandidatesTask, EvaluateBatchTask, ApplyGatesTask, SelectSurvivorsTask, RecordGenerationTask]`. A schedule (DOA-108) triggers it; all inter-task state flows through DOA-109 tables keyed by `generation_id` (no in-memory handoff, so a crashed generation is diagnosable and re-runnable).

- ✅ Dogfoods the orchestrator; every generation is visible in `workflow_runs` with per-stage status/timing for free.
- ✅ Crash semantics inherited from DOA-006: a failed generation is marked failed; rerun = trigger again (tasks are idempotent because state is keyed by generation_id + hashes).
- ✅ Budget enforcement is a config value checked in `GenerateCandidatesTask` (candidate cap) and `EvaluateBatchTask` (eval cap) — no new machinery.
- ❌ `EvaluateBatchTask` is one long task evaluating N candidates sequentially unless DOA-108 fan-out lands; acceptable at <1 s/eval (DOA-104 target) for ~100 candidates.
- ❌ Orchestrator has no inter-run chaining — "run generation N+1 after N" relies on the scheduler cadence, not causality (a slow generation could overlap the next; guard: controller refuses to start if the previous generation's run is still `running`).

### B. Dedicated long-lived asyncio loop service inside the backend process
A startup-launched `asyncio.Task` that sleeps, wakes, runs a generation in-process.

- ✅ No scheduler dependency; natural back-to-back chaining.
- ❌ Invisible to `workflow_runs` (or requires duplicating its bookkeeping); dies silently with the process; competes with the API event loop; reinvents exactly what the orchestrator exists to do.

### C. External driver (cron/GitHub Actions hits the trigger API)
- ✅ Minimal code: `curl -X POST /workflows/asil_generation/trigger` on a schedule.
- ✅ Keeps scheduling out of the app entirely (ops-friendly, easy to pause: disable the cron).
- ❌ Splits operational truth across systems (why didn't it run? check crontab + server + logs); secrets/URL management for the trigger; no in-app guard against overlapping runs unless we build it anyway.

**Recommendation:** **A**, with C as the interim trigger until DOA-108's in-app scheduler lands (the overlap guard is built either way).

## Selection policy (the "improving" semantics — decided here)

- **Fitness = validation-window score from DOA-107**, never the training-window score. Concretely: rank by validation Sharpe adjusted by the complexity penalty; ties → lower turnover wins (cheaper to run in reality).
- **Survivors:** top 10 by fitness that pass all hard gates. **Hall of fame:** top 3 all-time are never evicted (guards against regression when data updates shift scores).
- **Diversity guard:** at most 3 survivors sharing the same primary ranking metric — prevents the population collapsing into 10 flavors of "rank by ROCE".
- **Promotion:** a strategy that survives K=3 consecutive generations becomes `candidate_for_review` → human approval queue (DOA-111). The loop *nominates*; only humans *promote*.

## Budgets & stopping (runaway-compute protection, per epic risk #4)

- Per generation: ≤ 100 evaluations, ≤ 30 min wall clock (task exceeds → generation marked `failed:budget`).
- Per day: ≤ 3 generations (config), LLM proposer ≤ ₹X/day token budget when enabled.
- **Stagnation stop:** if best validation fitness hasn't improved by ≥2% over 10 generations, controller switches cadence to weekly and raises a `stagnated` flag to the UI — restarting aggressive search is a human decision (fresh data or new metrics warrant it; burning budget doesn't).
- **Data-gate:** a generation refuses to start if the latest `scrape_runs`/price ingest is `partial`/stale (>7 days) — evolving against rotten data is worse than pausing.

## Steps of completion

1. Implement the six tasks (thin wrappers around DOA-104/105/107/109 modules; all parameterized via DOA-014 instances, all repo I/O threadpooled per DOA-005).
2. Overlap guard: `LoadPopulationTask` fails fast if another `asil_generation` run is `running`.
3. Budget config in `Settings` (+ schema/env example): `ASIL_MAX_EVALS_PER_GEN`, `ASIL_MAX_GENS_PER_DAY`, `ASIL_STAGNATION_WINDOW`.
4. Generation record (DOA-109) written atomically at the end: population before/after, budget spent, best fitness, stagnation counter.
5. Failure drill: kill the process mid-generation; verify rerun completes cleanly with no duplicate evaluations (idempotency by hash).

## Acceptance criteria

- [ ] Three consecutive scheduled generations run unattended; each visible as a `workflow_runs` row with 6 task rows.
- [ ] Best validation fitness is non-decreasing across those generations *or* the immigration/diversity metrics explain why (recorded, not implied).
- [ ] Exceeding the eval budget stops the generation with `failed:budget`, population unchanged.
- [ ] Overlap guard proven: triggering twice concurrently → second run fails immediately with a clear error.
- [ ] Stagnation flag fires in a synthetic test (frozen data, 10 generations).

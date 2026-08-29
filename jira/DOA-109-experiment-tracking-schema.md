# DOA-109: Experiment tracking — strategies, evaluations, generations, lineage

- **Type:** Task (data model)
- **Priority:** P0 within epic DOA-100 (M1)
- **Component:** backend/db
- **Depends on:** DOA-103 (spec + hash); consumed by DOA-104/105/106/107/110

## Problem

The loop's memory. Every strategy ever tried, every evaluation ever run, every generation's population and decisions must be recorded — this is simultaneously (a) the loop's working state between generations (per DOA-108 capability-1 decision B), (b) the dedup/trials-count source DOA-107's statistics depend on, and (c) the audit trail the UI and the human reviewer read. If this is sloppy, the guardrails' math is wrong and the product's honesty claim collapses.

## Approaches considered for the storage model

**A. Bespoke relational schema in Supabase (below) — *recommended*.**
- ✅ One database (already operated); SQL joins power the UI directly; DB constraints *enforce* integrity rules the epic depends on (one holdout burn, no duplicate hashes) rather than trusting app code.
- ❌ We design and migrate it ourselves.

**B. Adopt MLflow/W&B-style experiment tracker.**
- ✅ Rich run-comparison UIs for free.
- ❌ Wrong shape (ML training runs ≠ strategy populations with lineage/gates); another service + auth to operate; the leaderboard UI we want is bespoke anyway (DOA-110); constraints like holdout-burn uniqueness don't exist there.

**C. JSON blobs in `workflow_task_runs.error`-style columns / files on disk.**
- ❌ Unqueryable, unconstrained, unjoinable. Listed only to reject.

## Schema (one migration)

```sql
CREATE TABLE strategies (
    strategy_hash text PRIMARY KEY,              -- canonical hash (DOA-103)
    spec jsonb NOT NULL,
    schema_version int NOT NULL,
    complexity int NOT NULL,
    origin text NOT NULL,                        -- template|mutation|crossover|immigration|llm|manual
    parent_hashes text[] NOT NULL DEFAULT '{}',  -- lineage
    english_summary text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by_generation bigint                  -- NULL for manual/seed
);

CREATE TABLE evaluations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_hash text NOT NULL REFERENCES strategies(strategy_hash),
    window_name text NOT NULL,                   -- train|validation|holdout|walkforward:<k>|sensitivity:<param>
    window_start date NOT NULL,
    window_end date NOT NULL,
    data_fingerprint text NOT NULL,              -- from DOA-104 (max as_of + row counts)
    metrics jsonb NOT NULL,                      -- CAGR, sharpe, drawdown, turnover, ...
    equity_curve jsonb NOT NULL,                 -- monthly points
    diagnostics jsonb NOT NULL,                  -- exclusions, portfolio sizes
    engine_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (strategy_hash, window_name, data_fingerprint)   -- idempotent re-eval
);

-- The holdout-burn registry (DOA-107): one holdout eval per strategy per epoch, forever.
CREATE TABLE holdout_burns (
    strategy_hash text NOT NULL REFERENCES strategies(strategy_hash),
    holdout_epoch text NOT NULL,                 -- e.g. '2026H1'
    evaluation_id uuid NOT NULL REFERENCES evaluations(id),
    passed boolean NOT NULL,
    PRIMARY KEY (strategy_hash, holdout_epoch)
);

CREATE TABLE generations (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workflow_run_id uuid REFERENCES workflow_runs(id),
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status text NOT NULL DEFAULT 'running',      -- running|completed|failed|failed:budget
    candidates_generated int,
    evaluations_spent int,
    best_fitness numeric,
    stagnation_counter int NOT NULL DEFAULT 0,
    population_before text[] NOT NULL DEFAULT '{}',   -- survivor hashes in
    population_after text[] NOT NULL DEFAULT '{}',    -- survivor hashes out
    notes jsonb                                   -- origin-mix stats, skips, gate summary
);

CREATE TABLE strategy_status (
    strategy_hash text PRIMARY KEY REFERENCES strategies(strategy_hash),
    status text NOT NULL DEFAULT 'evaluated',    -- evaluated|survivor|candidate_for_review|approved|rejected|killed
    status_changed_at timestamptz NOT NULL DEFAULT now(),
    changed_by text NOT NULL DEFAULT 'loop',     -- 'loop' | user identifier (DOA-111)
    reason text
);
```

Design decisions & trade-offs:

- **Metrics as JSONB vs columns:** JSONB — the metric set will evolve with DOA-104/107; promote hot fields (validation Sharpe) to a generated column/index when the leaderboard query needs it, not before.
- **`data_fingerprint` in the eval uniqueness key:** the same strategy re-evaluated after new data arrives is a *new* fact, not a duplicate — this is what lets the hall-of-fame re-score honestly over time.
- **`engine_version`:** engine bug fixes change results; comparing evals across engine versions must be detectable (UI badge + excluded from trials counts within an epoch).
- **Lineage as `parent_hashes[]`** (not a join table): populations are small; array queries suffice for the UI's family tree; revisit if lineage analytics grow.
- **Immutability policy:** `strategies` and `evaluations` rows are never UPDATEd (except nothing) — corrections happen by new rows/epochs. `strategy_status` is the only mutable surface, and every change is written with actor + reason (append a `strategy_status_history` trigger if audit demands grow — deferred).
- **RLS:** locked to service key like everything else (DOA-009); the UI reads via our API, never Supabase-direct.

## Repository layer

`app/asil/repositories/`: `StrategyRepository`, `EvaluationRepository`, `GenerationRepository` — same conventions as existing repos (sync methods, models in/out, threadpooled by callers per DOA-005). Key queries to ship with tests:

- `leaderboard(limit, window='validation')` — top strategies by fitness with gate summary (backs DOA-110's main page).
- `trials_count(holdout_epoch)` — exact N for DOA-107's deflated Sharpe.
- `unexplored(hashes: list[str]) -> list[str]` — dedup filter for DOA-105.
- `lineage(strategy_hash, depth=3)` — family tree.

## Steps of completion

1. Migration above + RLS lockdown.
2. Pydantic models mirroring the tables (reuse `app/models/base.py` conventions).
3. Repositories + the four named queries, with fixture-based tests (no live DB — fake per DOA-010 pattern, plus one optional integration test gated on env).
4. Backfill hook: DOA-103's fixture strategies inserted as `origin='manual'` seeds.
5. Grafana-less observability: a `generation_summary` SQL view (one row per generation with key stats) — cheap dashboard until DOA-110.

## Acceptance criteria

- [ ] Inserting the same spec twice → single `strategies` row (PK conflict handled as no-op).
- [ ] Re-running an identical evaluation (same hash, window, fingerprint) → no new row (UNIQUE upsert), new fingerprint → new row.
- [ ] Second holdout burn for same hash+epoch → constraint violation surfaced as a typed error.
- [ ] `leaderboard()` returns in <200 ms with 10k strategies / 50k evaluations of synthetic data.
- [ ] Every `strategy_status` change records actor and reason.

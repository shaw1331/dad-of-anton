# DOA-101: ASIL data foundation — point-in-time fundamentals snapshots in Supabase

- **Type:** Task (platform)
- **Priority:** P0 within epic DOA-100 (M0)
- **Component:** screener_scraper, backend/db
- **Depends on:** DOA-001 (client fail-fast), DOA-009 (service-role key — this data is the product's crown jewels)

## Problem

The loop needs to query "what did we know about company X **as of date D**" — and today scraped data lives in throwaway CSVs (`screener_scraper/output/*.csv`, gitignored, overwritten every run). Without point-in-time (PIT) snapshots, every backtest silently uses *today's* fundamentals for *past* decisions — look-ahead bias that invalidates the entire product.

## Requirements

1. Every scrape run persists a **snapshot**: (company, metric, value, `as_of` date, source run id).
2. History is append-only; re-scraping a day upserts idempotently (same `as_of` → overwrite, different → new row).
3. Universe membership is also PIT: which tickers were in SMALLCAP50 *on date D* (indexes change composition — survivorship bias otherwise).
4. Queryable joins with price data (DOA-102) by `(ticker, date)`.

## Approaches

### A. Keep CSVs; add an importer task in the backend that loads them into Supabase
The scraper stays untouched; a new `ImportScrapeTask` (workflow task) reads `output/*.csv` and upserts.

- ✅ Zero risk to the working scraper; scraper remains usable standalone/offline.
- ✅ Import logic lives in the backend where the Supabase client, models, and retries already exist (post DOA-001).
- ✅ Natural first real workflow for the orchestrator ("scrape-import" pipeline).
- ❌ Two-step fragility: CSVs are an implicit contract (column drift breaks silently — mitigate with a schema check on import).
- ❌ Scraper and backend must share a filesystem (fine today, blocks containerized split later).

### B. Scraper writes directly to Supabase
Add `supabase-py` to `screener_scraper/requirements.txt`; `save_to_csv` gains a `save_to_db` sibling.

- ✅ One step, no file contract, works from the Windows box (`run.bat` exists — scraper runs somewhere else today).
- ❌ Couples the standalone scraper to backend infra + secrets (service key on the scrape machine — worse security surface).
- ❌ Duplicate DB code in two codebases with different conventions (`memory.md` even forbids type hints there).
- ❌ Harder to test; network failures mid-scrape leave partial snapshots without the backend's transaction discipline.

### C. Fold the scraper into the backend as workflow tasks (scrape + persist in-process)
`ScrapeIndexTask`, `ScrapeCompaniesTask` become backend workflow tasks.

- ✅ The end-state architecture: one deployable, full observability via `workflow_task_runs`, retries per task, no CSV contract.
- ✅ Loop and data collection share one scheduler and one config system.
- ❌ Big-bang migration of 600 lines of scraping code mid-epic; blocks M0 on a refactor.
- ❌ Long scrapes (250 companies × 1.5 s delay ≈ 7 min minimum) inside BackgroundTasks stresses the orchestrator before DOA-005/006 land.

**Recommendation:** **A now, C later.** A ships M0 in days with near-zero risk; C is the target once the orchestrator hardening (DOA-005/006/014) and this epic's M1 are proven. B is rejected outright (secret sprawl).

## Schema (new migration)

```sql
CREATE TABLE scrape_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    as_of date NOT NULL,
    source text NOT NULL DEFAULT 'screener.in',
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status text NOT NULL DEFAULT 'running'   -- running|completed|failed|partial
);

CREATE TABLE index_constituents (
    scrape_run_id uuid NOT NULL REFERENCES scrape_runs(id),
    as_of date NOT NULL,
    index_name text NOT NULL,
    ticker text NOT NULL,
    company_name text NOT NULL,
    PRIMARY KEY (as_of, index_name, ticker)
);

CREATE TABLE fundamentals_snapshots (
    scrape_run_id uuid NOT NULL REFERENCES scrape_runs(id),
    as_of date NOT NULL,
    ticker text NOT NULL,
    metric text NOT NULL,          -- e.g. 'ROCE', 'Stock P/E' (from config.py labels)
    value_numeric numeric,         -- parsed when possible
    value_text text,               -- raw fallback (Pros/Cons, High/Low)
    PRIMARY KEY (as_of, ticker, metric)
);
CREATE INDEX idx_fund_snap_ticker ON fundamentals_snapshots(ticker, metric, as_of);
```

Design notes with trade-offs:

- **EAV (metric rows) vs wide table (one column per metric):** EAV chosen — the metric list lives in `config.py` and changes often; wide tables need a migration per new metric. Cost: clumsier SQL (pivot needed) and no per-metric types — mitigated by `value_numeric`/`value_text` split. Revisit as a materialized wide view if query pain appears.
- **`(as_of, ticker, metric)` PK** gives idempotent re-imports for free (`upsert`).
- **Partial runs must be marked `partial`** (ties into DOA-012's complete-flag) so backtests can exclude tainted dates.

## Steps of completion

1. Migration above (`2026MMDDNNNNNN_create_asil_snapshot_tables.sql`), RLS enabled + no permissive policies (service key only, per DOA-009).
2. Backend: `app/asil/importer.py` — parse `*_companies.csv` + `*_data.csv`, numeric coercion (strip `₹ , % Cr.`), upsert, mark run status.
3. `ImportScrapeTask(BaseWorkflowTask)` + register a `scrape_import` workflow (uses DOA-014 parameterized instances).
4. Backfill: import the CSVs currently on disk as the first snapshot (best-effort `as_of` = file mtime, flagged `source='backfill'`).
5. Data-quality checks in the importer: row counts vs constituent counts, ≥95% numeric-parse rate on numeric metrics, else run = `partial`.
6. Tests: parser unit tests with real CSV fixtures; idempotency test (import twice → same row count).

## Acceptance criteria

- [ ] After a scrape + import, `SELECT count(*) FROM fundamentals_snapshots WHERE as_of = current_date` ≈ tickers × metrics.
- [ ] Re-running the import is a no-op (identical counts, updated values).
- [ ] Index membership for a given date reproduces the scraped CSV exactly.
- [ ] A deliberately truncated CSV yields a `partial` run and a visible warning, not silent data.

## Open questions

- Historical fundamentals (quarterly results tables on screener) — scrape deeper history now or accept snapshot-forward-only? *PM stance: snapshot-forward for M0; deep-history scrape is a separate ticket if DOA-104 shows we're data-starved.*

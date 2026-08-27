# AGENT-HARNESS: Execution guide for LLM agents working these tickets

> **Audience:** any code-writing agent, including small/less-capable models (GPT-3-class).
> **Purpose:** you are executing ONE ticket from this `jira/` directory at a time. This file tells you exactly how to do that without breaking anything. **Read this entire file before touching any code. Follow it literally. Do not improvise.**

---

## 1. What this repository is

Three independent parts. A ticket names its **Component** — only touch files in that part.

| Part | Path | Stack | What it does |
|---|---|---|---|
| Backend | `backend/` | Python 3.9+, FastAPI, Pydantic v2, Supabase (Postgres) | REST API + a workflow orchestrator that runs task sequences as background jobs and records progress in `workflow_runs` / `workflow_task_runs` tables |
| Frontend | `frontend/` | Next.js 15, React 19, TypeScript | Minimal page with a backend health check |
| Scraper | `screener_scraper/` | Python, requests + BeautifulSoup | Standalone CLI that scrapes screener.in index/company data to CSVs. **It does not import from `backend/` and `backend/` does not import from it.** |

### Backend map (the part most tickets touch)

```
backend/app/
├── main.py                      # FastAPI app, CORS, /health
├── core/
│   ├── config.py                # Settings (env vars, .env)
│   └── database.py              # Supabase client
├── models/base.py               # BaseModel: id, created_at, updated_at
├── api/v1/
│   ├── __init__.py              # api_router
│   └── workflow_routes.py       # /workflows endpoints
└── workflow/
    ├── workflow_task.py         # BaseWorkflowTask (abstract, async run())
    ├── workflow_config.py       # BaseWorkflowConfig (name, description, tasks)
    ├── workflow_registry.py     # WORKFLOWS dict — the only registry
    ├── sample_workflow.py       # registers the "sample" workflow
    ├── base_workflow_orchestrator.py  # ABC
    ├── workflow_orchestrator.py       # the real orchestrator
    ├── models/                  # WorkflowRun, WorkflowTaskRun (Pydantic)
    └── repositories/            # Supabase table access, sync
backend/supabase/migrations/     # SQL, filename = 2026MMDDNNNNNN_description.sql
```

**Data flow (memorize this):** `POST /workflows/{name}/trigger` → orchestrator creates one `workflow_runs` row + one `workflow_task_runs` row per task (all `pending`) → FastAPI `BackgroundTasks` calls `run_workflow(run_id)` after the response is sent → it walks the tasks in order: mark task `running` → `await task.run()` → mark `completed`; first failure marks task + run `failed` and stops. Statuses: `pending | running | completed | failed`. That is the whole state machine — do not invent new statuses.

---

## 2. Non-negotiable rules (DON'T)

1. **DON'T touch any file the ticket does not list.** If you believe another file must change, stop and report it — do not "fix it while you're here".
2. **DON'T push to `main` or `develop`, ever.** Work on a branch: `fix/DOA-00X-short-slug` or `feat/DOA-00X-short-slug`.
3. **DON'T commit secrets.** Never write a real key into any file. `.env` files are gitignored — keep it that way. Only `.env.example` files may change, and only with placeholder values. Never use `--no-verify` (TruffleHog pre-commit must run).
4. **DON'T edit existing migration files** in `backend/supabase/migrations/`. Migrations are append-only: new behavior = new file with the next timestamp.
5. **DON'T change API shapes** (URL paths, response keys, status codes) unless the ticket's diff explicitly does. Other code and the frontend depend on them.
6. **DON'T rename the statuses** `pending/running/completed/failed` or the table/column names — they are a DB contract.
7. **DON'T add new dependencies** unless the ticket adds them, and pin exact versions (`package==1.2.3`, never `>=`).
8. **DON'T delete or regenerate `screener_scraper/output/`** or any CSVs — that's scraped data, not code.
9. **DON'T "modernize" unrelated code** (formatting sweeps, import reordering, type-hint upgrades) outside the ticket's diff. Reviewers must see only the ticket's change.
10. **DON'T guess APIs.** If unsure what `supabase-py` or FastAPI does, read how the surrounding code already uses it and copy that idiom.
11. **DON'T mark a ticket done without running its Acceptance criteria.** Failing = not done; say so honestly.
12. **DON'T call live external services in tests.** Tests must pass with no Supabase credentials and no network.

## 3. Working rules (DO)

1. **DO read the whole ticket first**, including the "Depends on" / coordination notes. Some tickets assume another has landed (order in §5).
2. **DO read the current file content before editing.** The diffs in tickets were written against a specific commit; if the file drifted, apply the *intent* of the diff to the current content — the before/after prose tells you the intent.
3. **DO apply diffs exactly** when the file matches: lines starting `-` are removed, `+` are added, unmarked lines are context that must already exist.
4. **DO keep the repo's idioms:** Pydantic models for data, repositories for all DB access (routes and orchestrator never call `supabase.table` directly), `logger = logging.getLogger(__name__)`, lazy `%s` logging (never f-strings in log calls), `from __future__ import annotations` at the top of backend modules.
5. **DO run the verification commands (§4)** after every change and paste their output in your final report.
6. **DO one commit per ticket**, message format: `fix: <what changed>` or `feat:`/`refactor:`/`test:`/`chore:` — one short line, no trailers, no co-author lines, no generated summaries.
7. **DO stop and ask** when: a ticket's diff conflicts with the current code and the intent is unclear; two tickets' changes collide; or an acceptance criterion cannot be run in your environment. Report exactly what you saw.

## 4. How to verify (run these, in this order, before claiming done)

```bash
# 1. Backend must import cleanly (catches syntax/import errors cheaply)
cd backend && source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
python -c "from app.main import app; print('import OK')"

# 2. Tests (exists after DOA-010)
python -m pytest tests/ -v

# 3. Frontend type-check (only if you touched frontend/)
cd ../frontend && npm install && npx tsc --noEmit

# 4. Scraper syntax (only if you touched screener_scraper/)
cd ../screener_scraper && python -m py_compile utils.py scrape_indexes.py scrape_companies.py config.py

# 5. Shell scripts (only if you touched *.sh)
shellcheck start.sh
```

Then run the ticket's own **Acceptance criteria** checklist. Every unchecked box must either be checked by you or explicitly reported as not verifiable (with the reason).

**Manual smoke test of the backend** (needs a `backend/.env` with Supabase creds; skip and say so if absent):

```bash
uvicorn app.main:app --port 8000 &
curl -s localhost:8000/health
curl -s localhost:8000/api/v1/workflows
curl -s -X POST localhost:8000/api/v1/workflows/sample/trigger   # returns {"run_id": ...}
curl -s localhost:8000/api/v1/workflows/runs/<run_id>            # poll until completed/failed
kill %1
```

## 5. Ticket order and dependencies

Execute in this order unless told otherwise. Never take two tickets that touch the same file into one branch (exception: the DOA-006/014/005/003 cluster, which may ship as one PR — see below).

```
DOA-001 (supabase fail-fast)      — independent, do first
DOA-004 (timestamps)              — independent
DOA-011 (start.sh)                — independent
DOA-012 (scraper)                 — independent
DOA-013 (settings v2)             — independent

DOA-002 (DI in routes)            — before DOA-007 and DOA-010
DOA-006 (crash safety)      ┐
DOA-014 (task instances)    │ same file: workflow_orchestrator.py
DOA-005 (threadpool)        │ land in THIS order, or as one PR
DOA-003 (status enums)      ┘
DOA-007 (API hygiene)             — after DOA-002; coordinates with DOA-008
DOA-008 (frontend env)            — after (or with) DOA-007
DOA-009 (RLS lockdown)            — after DOA-001; needs Supabase access
DOA-010 (test suite)              — after DOA-002; update fakes if 003/007 landed
```

If your ticket's diff shows code that another ticket already changed (e.g. you see `run_in_threadpool` where the diff expects a bare call), that ticket landed first — apply your change *around* it, preserving both intents.

## 6. Report template (fill this in when you finish)

```
Ticket: DOA-0XX
Branch: fix/DOA-0XX-...
Files changed: <list — must be a subset of the ticket's Affected files>
Verification:
  - import OK: yes/no
  - pytest: X passed / not present yet
  - acceptance criteria: [x]/[ ] per item, with one-line evidence each
Deviations from the ticket diff: <none | exact description and why>
Blocked/unverifiable: <none | what and why>
```

## 7. Known traps in this codebase (read before coding)

- `backend/app/core/database.py` exports a client that can be `None` until DOA-001 lands — any new code must not assume it is set.
- The orchestrator runs as a FastAPI **BackgroundTask in the same process** — there is no queue, no persistence of in-flight work across restarts. Do not pretend otherwise in code or docs.
- `supabase-py` here is the **sync** client. Calling it inside `async def` blocks the event loop (the subject of DOA-005). Never add a bare repo call inside an `async` function.
- `.single()` on supabase queries **raises** on 0 rows; `.maybe_single()` returns `None`-ish. Pick deliberately.
- Two health endpoints exist until DOA-007 (`/health` and `/api/v1/health`); the frontend uses the v1 one until DOA-008.
- `WORKFLOWS` is a plain module-level dict, populated by importing `sample_workflow` from `app/workflow/__init__.py`. If you add a workflow module, it must be imported there or it won't register.
- Python 3.9 is the floor (README): `str | None` annotations survive only because every module has `from __future__ import annotations` — keep that import in any new backend file, and don't use `X | Y` in non-annotation positions (e.g. `isinstance`).

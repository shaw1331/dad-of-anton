# Agent Instructions

## Git Workflow

- **Never push directly to `main`.** Always create a feature branch, commit there, and open a PR for review.
- Branch naming: `feat/<description>`, `fix/<description>`, or `chore/<description>`
- Keep commits focused and use conventional commit messages (`feat:`, `fix:`, `refactor:`, `chore:`, etc.)

## Architecture

- **Backend**: FastAPI (Python 3.11+) at `backend/`, runs on port 8000
- **Frontend**: Next.js 15 + React 19 at `frontend/`, runs on port 3000
- **Database**: Supabase (PostgreSQL). Migrations in `backend/supabase/migrations/` — append-only, new behavior = new file with next timestamp
- **LLM**: Configurable via `LLM_PROVIDER` env var. Default is Ollama (local). LangChain's `init_chat_model` handles provider abstraction.

### Workflow System

Core pattern in the backend. Key files:

- `backend/app/workflow/workflow_orchestrator_v1/workflow_registry.py` — `WORKFLOWS` dict where all workflows register
- `backend/app/workflow/base_workflow_config.py` — `BaseWorkflowConfig` dataclass (name, tasks, input_fields)
- `backend/app/workflow/base_workflow_task.py` — `BaseWorkflowTask` ABC with `run(ctx)` method
- `backend/app/workflow/workflow_orchestrator_v1/workflow_orchestrator.py` — `WorkflowOrchestrator` with `create_run()`, `trigger_workflow()`, `run_workflow()`

**To add a workflow**: Create a module that defines a `BaseWorkflowConfig` and appends it to `WORKFLOWS`. Import it from `backend/app/workflow/__init__.py` to auto-register.

**Trigger flow**: `POST /api/v1/workflows/{name}/trigger` → `trigger_workflow()` creates DB records → background task runs `run_workflow()` sequentially through tasks.

**Scheduled runs**: `backend/app/scheduler/` uses APScheduler (runs in-process with FastAPI). Configured for daily 09:00 IST. Edit `SCHEDULED_INDICES` in `jobs.py` to change what runs.

### Backend Code Conventions

- `from __future__ import annotations` at top of every module
- Lazy `%s` logging: `logger.info("Found %d stocks", len(stocks))` (not f-strings)
- Factory pattern: `ScraperFactory`, `AgentFactory`, `AnalysisFactory` — all classmethods with `_registry` dicts
- Repository pattern for DB access — never call `supabase.table()` directly from routes
- Custom exception hierarchy: `AnalysisError -> GraphError, ConfigError`
- Generic result types: `ScraperResult[T]`, `AgentResult[T]`

## Running

### Local development

```bash
# Backend
cd backend && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Or use `./start.sh` from the project root (starts both).

### Docker

```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

Ollama runs on the host. Docker containers reach it via `host.docker.internal:11434` (configured in `docker-compose.yml`).

### Verification commands

```bash
# Import check
cd backend && source venv/bin/activate
python -c "from app.main import app; print('OK')"

# Smoke test
curl -s localhost:8000/health
curl -s localhost:8000/api/v1/workflows

# Frontend proxy check (Docker)
docker compose exec frontend wget -qO- http://localhost:3000/api/v1/health
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Required:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous key |
| `LLM_PROVIDER` | `ollama`, `groq`, `openai`, `google_genai`, `anthropic`, `openrouter` |
| `LLM_MODEL` | Model name (e.g., `llama3`) |
| `OLLAMA_BASE_URL` | Only if Ollama is not on `localhost:11434` |

## Testing

```bash
cd backend && python -m pytest tests/ -v
```

**Warning**: Existing tests are integration tests that call a live LLM. There are no unit tests or mocks. A running LLM provider (e.g., Ollama) is required.

## Frontend Notes

- API calls proxy through Next.js rewrites (`/api/v1/*` → backend). The `API_URL` env var is baked at **build time** — in Docker, pass it as a build arg.
- Dark mode uses Tailwind `class` strategy with custom tokens (`dark-bg`, `dark-surface`, `dark-border`, `dark-text`, `dark-muted`).
- TypeScript strict mode. No additional UI libraries — raw Tailwind.

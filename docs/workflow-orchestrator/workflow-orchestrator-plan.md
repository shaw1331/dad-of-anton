# Workflow Orchestrator Plan

## Design Decisions

- **Config format**: Python dataclasses (type-safe, no extra deps)
- **Execution**: FastAPI `BackgroundTasks` (simple, no Redis/Celery)
- **Task registry**: Base class `BaseWorkflowTask` with `run()` method
- **UI**: Plain React pages (matches current project style, no new CSS lib)

---

## Part 1: Database Schema (Supabase)

Two tables needed:

### `workflow_runs` - tracks each workflow execution

| Column | Type | Notes |
|---|---|---|
| `id` | uuid (PK) | Unique `runId` |
| `workflow_name` | text | Name of the workflow config |
| `status` | text | `pending`, `running`, `completed`, `failed` |
| `current_task_index` | int | Which step it's at (0-indexed) |
| `total_tasks` | int | Total steps in the workflow |
| `error` | text | Error message if failed |
| `created_at` | timestamptz | Auto |
| `updated_at` | timestamptz | Auto |

### `workflow_task_runs` - tracks each task execution within a workflow

| Column | Type | Notes |
|---|---|---|
| `id` | uuid (PK) | Unique `taskId` |
| `workflow_run_id` | uuid (FK) | References `workflow_runs.id` |
| `task_name` | text | Name of the task class |
| `task_index` | int | Position in the workflow |
| `status` | text | `pending`, `running`, `completed`, `failed` |
| `error` | text | Error message if failed |
| `started_at` | timestamptz | When task started |
| `completed_at` | timestamptz | When task finished |
| `created_at` | timestamptz | Auto |

---

## Part 2: Backend - Core Workflow Engine

### `backend/app/workflow/workflow_config.py` - BaseWorkflowConfig and workflow registry

```python
@dataclass
class BaseWorkflowConfig:
    name: str
    description: str
    tasks: list[type[BaseWorkflowTask]]  # ordered list of task classes

# Registry to hold all defined workflows
WORKFLOWS: dict[str, BaseWorkflowConfig] = {}
```

### `backend/app/workflow/workflow_task.py` - Base BaseWorkflowTask class

```python
class BaseWorkflowTask(ABC):
    name: str  # human-readable name

    @abstractmethod
    async def run(self) -> None:
        """Execute the task. Raise exceptions on failure."""
        pass
```

### `backend/app/workflow/workflow_runner.py` - Orchestrator logic

- `trigger_workflow(workflow_name) -> workflow_run_id`: Creates DB records, kicks off BackgroundTasks
- `run_workflow(run_id)`: Iterates through tasks, updates status in DB, catches errors

### `backend/app/workflow/__init__.py` - Exports

---

## Part 3: Backend - API Endpoints

Add a new router at `backend/app/api/v1/workflow_routes.py`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/workflows` | List all registered workflow configs |
| `POST` | `/workflows/{name}/trigger` | Trigger a new workflow run |
| `GET` | `/workflows/runs` | List all workflow runs (with status) |
| `GET` | `/workflows/runs/{run_id}` | Get a single run with its task details |

---

## Part 4: Backend - File Structure

```
backend/app/
├── workflow/
│   ├── __init__.py              # exports
│   ├── workflow_config.py       # BaseWorkflowConfig dataclass + WORKFLOWS registry
│   ├── workflow_task.py         # BaseWorkflowTask base class
│   └── workflow_runner.py       # trigger_workflow(), run_workflow()
├── api/v1/
│   ├── __init__.py              # add workflow router
│   └── workflow_routes.py       # API endpoints
└── models/
    └── (unused - using Supabase directly, no ORM models)
```

---

## Part 5: Frontend - Pages

### `frontend/app/workflows/page.tsx` - Main workflows page

- Lists all registered workflows with a "Trigger" button
- Lists recent workflow runs with status badges

### `frontend/app/workflows/[runId]/page.tsx` - Run detail page

- Shows workflow name, status, progress (e.g., "Step 3/7")
- Lists all tasks with their individual status, start/end times

### `frontend/app/components/WorkflowList.tsx` - Workflow configs list
### `frontend/app/components/WorkflowRunList.tsx` - Recent runs list
### `frontend/app/components/WorkflowRunDetail.tsx` - Run detail view

Frontend file structure:

```
frontend/app/
├── workflows/
│   ├── page.tsx                        # /workflows - list view
│   └── [runId]/
│       └── page.tsx                    # /workflows/:runId - detail view
├── components/
│   ├── HealthCheck.tsx                 # (existing)
│   ├── WorkflowList.tsx                # List of workflow configs
│   ├── WorkflowRunList.tsx             # List of runs
│   └── WorkflowRunDetail.tsx          # Run detail with task progress
```

---

## Part 6: Implementation Order

1. **Database**: Create Supabase tables (manual SQL or via Supabase dashboard)
2. **Backend workflow engine**: `workflow_config.py`, `workflow_task.py`, `workflow_runner.py`
3. **Backend API**: `workflow_routes.py` endpoints + register router
4. **Frontend**: Workflow list page, trigger button, run detail page
5. **Test**: Create a sample workflow with 2-3 dummy tasks to verify end-to-end

---

## Sample Workflow Example

```python
class PrintTask(BaseWorkflowTask):
    name = "print_message"
    async def run(self):
        print("Hello from task!")

class DelayTask(BaseWorkflowTask):
    name = "delay"
    async def run(self):
        await asyncio.sleep(2)

# Register
WORKFLOWS["sample"] = BaseWorkflowConfig(
    name="sample",
    description="A sample workflow",
    tasks=[PrintTask, DelayTask, PrintTask]
)
```

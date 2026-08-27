# Workflow Inputs - Design Plan

## Problem

The current workflow orchestrator is static — tasks are instantiated with `task_cls()` (no arguments), `run()` returns `None`, and the trigger endpoint accepts no payload. There is no way for users to pass input data to a workflow.

## Goal

Allow each workflow to declare an **input schema** (variable fields), accept user-provided values at trigger time, validate them, persist them, and pass them to the workflow's tasks via a shared context object.

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Input schema format | `InputField` dataclass list | Lightweight, flexible, easy to render dynamically on frontend |
| Data delivery mechanism | `BaseWorkflowContext` object | Uniform interface for all tasks, extensible for future task output flow |
| Input validation | Server-side in orchestrator | Centralized, consistent error messages |
| Storage | JSONB column on `workflow_runs` | Audit trail, debugging, replay capability |
| Backward compatibility | Defaults to empty list/None | Existing workflows and tasks work without changes |

---

## Part 1: Input Schema Definition

### `InputField` dataclass

Add to `backend/app/workflow/workflow_config.py`:

```python
@dataclass
class InputField:
    name: str           # key used in the input dict
    type: str           # "str" | "int" | "float" | "bool" | "text"
    label: str          # human-readable label for UI
    description: str = ""
    required: bool = True
    default: Any = None
```

### Updated `BaseWorkflowConfig`

```python
@dataclass
class BaseWorkflowConfig:
    name: str
    description: str
    tasks: list[type[BaseWorkflowTask]] = field(default_factory=list)
    input_fields: list[InputField] = field(default_factory=list)  # NEW
```

### Example usage

```python
WORKFLOWS["greet"] = BaseWorkflowConfig(
    name="greet",
    description="Greet a user with a custom message",
    input_fields=[
        InputField(name="name", type="str", label="Name", description="User's name"),
        InputField(name="greeting", type="str", label="Greeting", required=False, default="Hello"),
    ],
    tasks=[GreetTask],
)
```

Workflows with no inputs omit `input_fields` — defaults to `[]`, fully backward compatible.

---

## Part 2: BaseWorkflowContext

### New file: `backend/app/workflow/base_workflow_context.py`

```python
class BaseWorkflowContext:
    """Shared context passed through all tasks in a workflow run."""

    def __init__(self, input: dict[str, Any]) -> None:
        self.input = input
        self._outputs: dict[str, Any] = {}

    def get_input(self, key: str) -> Any:
        return self.input.get(key)

    def set_output(self, task_name: str, value: Any) -> None:
        self._outputs[task_name] = value

    def get_output(self, task_name: str) -> Any:
        return self._outputs.get(task_name)
```

**Why a context object instead of just passing `input` directly?**
- Uniform interface — every task receives the same `ctx` parameter
- Enables future data flow — tasks can read outputs from previous tasks
- Clean separation — input is immutable, outputs are accumulated
- No signature changes needed when adding task output flow later

---

## Part 3: Backend Changes

### 3.1 `BaseWorkflowTask.run()` signature change

**File:** `backend/app/workflow/workflow_task.py`

```python
# Before
async def run(self) -> None: ...

# After
async def run(self, ctx: BaseWorkflowContext) -> None: ...
```

This is a **breaking change** for all existing tasks. Each task must add `ctx` as a parameter (can ignore it initially).

### 3.2 `BaseWorkflowOrchestrator` signature update

**File:** `backend/app/workflow/base_workflow_orchestrator.py`

```python
# Before
def trigger_workflow(self, workflow_name: str, background_tasks: BackgroundTasks) -> str: ...

# After
def trigger_workflow(self, workflow_name: str, background_tasks: BackgroundTasks, input_data: dict | None = None) -> str: ...
```

### 3.3 `WorkflowOrchestrator` changes

**File:** `backend/app/workflow/workflow_orchestrator.py`

**`trigger_workflow()`:**
1. Accept optional `input_data: dict | None = None`
2. Validate input against `config.input_fields`:
   - Check all `required=True` fields are present
   - Attempt type coercion (str → int, str → float, etc.)
   - Return clear error on validation failure
3. Store `input_data` in the `WorkflowRun` record

**`run_workflow()`:**
1. Read `input` from the `WorkflowRun` record (fetched from DB)
2. Create `BaseWorkflowContext(input=run.input or {})`
3. Pass `ctx` to each task: `await task_instance.run(ctx)`
4. (Future: capture task outputs via return values)

### 3.4 Input validation logic

```python
def validate_input(self, config: BaseWorkflowConfig, input_data: dict) -> dict:
    """Validate and coerce input data against workflow's input_fields."""
    validated = {}
    for field in config.input_fields:
        if field.name in input_data:
            value = input_data[field.name]
            validated[field.name] = coerce_type(value, field.type)
        elif field.required and field.default is None:
            raise ValueError(f"Missing required field: {field.name}")
        elif field.default is not None:
            validated[field.name] = field.default
    return validated
```

Type coercion rules:
- `str`: pass through ( stringify non-str )
- `int`: `int(value)`
- `float`: `float(value)`
- `bool`: `str(value).lower() in ("true", "1", "yes")`
- `text`: pass through ( multi-line string )

---

## Part 4: Database Changes

### New migration: `20260827000004_add_input_to_workflow_runs.sql`

```sql
ALTER TABLE workflow_runs ADD COLUMN input jsonb;
```

### `WorkflowRun` model update

**File:** `backend/app/workflow/models/workflow_run.py`

```python
class WorkflowRun(BaseModel):
    workflow_name: str
    status: str
    current_task_index: int
    total_tasks: int
    error: str | None = None
    input: dict | None = None  # NEW
```

No changes needed to `WorkflowRunRepository` — `model_dump()` and `model_validate()` handle the new field automatically.

---

## Part 5: API Changes

### `POST /workflows/{name}/trigger`

**Request body:**
```json
{
  "input": {
    "name": "Alice",
    "greeting": "Hi"
  }
}
```

**New Pydantic request model:**
```python
class TriggerRequest(BaseModel):
    input: dict[str, Any] = {}
```

**Response:** `{"run_id": "..."}` (unchanged)

**Error (422):**
```json
{
  "detail": "Missing required field: name"
}
```

### `GET /workflows`

**Updated response:**
```json
[
  {
    "name": "greet",
    "description": "Greet a user",
    "task_count": 1,
    "input_fields": [
      {"name": "name", "type": "str", "label": "Name", "description": "User's name", "required": true, "default": null},
      {"name": "greeting", "type": "str", "label": "Greeting", "description": "", "required": false, "default": "Hello"}
    ]
  }
]
```

### `GET /workflows/runs/{run_id}`

**Updated response** — adds `input` field:
```json
{
  "id": "...",
  "workflow_name": "greet",
  "status": "completed",
  "input": {"name": "Alice", "greeting": "Hi"},
  "task_runs": [...]
}
```

---

## Part 6: Frontend Changes

### 6.1 Updated types

**File:** `frontend/lib/types.ts`

```typescript
export interface InputField {
  name: string;
  type: "str" | "int" | "float" | "bool" | "text";
  label: string;
  description: string;
  required: boolean;
  default: any | null;
}

export interface WorkflowConfig {
  name: string;
  description: string;
  task_count: number;
  input_fields: InputField[];  // NEW
}

export interface RunDetail extends WorkflowRun {
  task_runs: TaskRun[];
  input: Record<string, any> | null;  // NEW
}
```

### 6.2 Updated API client

**File:** `frontend/lib/api/workflows.ts`

```typescript
export async function triggerWorkflow(
  workflowName: string,
  input?: Record<string, any>
): Promise<{ run_id: string }> {
  return request(`/workflows/${workflowName}/trigger`, {
    method: "POST",
    body: JSON.stringify({ input: input ?? {} }),
  });
}
```

### 6.3 Dynamic input form

**File:** `frontend/app/workflows/page.tsx`

When a workflow has `input_fields.length > 0`:
- "Trigger" button opens a modal/dialog instead of triggering immediately
- Modal renders form fields dynamically:
  - `type: "str"` → `<input type="text">`
  - `type: "int"` → `<input type="number" step="1">`
  - `type: "float"` → `<input type="number" step="0.01">`
  - `type: "bool"` → `<input type="checkbox">`
  - `type: "text"` → `<textarea>`
- Each field shows its `label`, `description` as help text, and marks required fields with `*`
- Pre-fills `default` values
- On submit: validates required fields client-side, calls `triggerWorkflow(name, input)`
- On cancel: closes modal

Workflows with empty `input_fields` continue to trigger immediately (no regression).

### 6.4 Show input in run detail

**File:** `frontend/app/components/WorkflowRunDetail.tsx`

Add an "Input" section at the top of the run detail view:
- Renders input as key-value pairs (e.g., `name: Alice`, `greeting: Hi`)
- Only shown if `input` is non-null and non-empty
- Styled as a small info card above the task list

---

## Part 7: Sample Workflow Update

**File:** `backend/app/workflow/sample_workflow.py`

Update the sample workflow to demonstrate inputs:

```python
class PrintMessageTask(BaseWorkflowTask):
    name = "print_message"

    def __init__(self, message: str = "Hello from task!") -> None:
        self.message = message

    async def run(self, ctx: BaseWorkflowContext) -> None:
        message = ctx.get_input("message") or self.message
        print(message)


WORKFLOWS["sample"] = BaseWorkflowConfig(
    name="sample",
    description="A sample workflow with 3 dummy tasks",
    input_fields=[
        InputField(name="message", type="str", label="Message", description="Message to print", required=False, default="Hello from task!"),
    ],
    tasks=[PrintMessageTask, DelayTask, PrintMessageTask],
)
```

---

## File Change Summary

| File | Change Type | Description |
|---|---|---|
| `backend/app/workflow/workflow_config.py` | Modify | Add `InputField` dataclass, add `input_fields` to config |
| `backend/app/workflow/base_workflow_context.py` | **Create** | `BaseWorkflowContext` class |
| `backend/app/workflow/workflow_task.py` | Modify | Update `run()` signature to accept `ctx` |
| `backend/app/workflow/base_workflow_orchestrator.py` | Modify | Update `trigger_workflow` signature |
| `backend/app/workflow/workflow_orchestrator.py` | Modify | Accept, validate, persist input; create context; pass to tasks |
| `backend/app/workflow/models/workflow_run.py` | Modify | Add `input` field |
| `backend/app/api/v1/workflow_routes.py` | Modify | Accept input body, return input_fields |
| `backend/supabase/migrations/20260827000004_*.sql` | **Create** | Add `input` JSONB column |
| `frontend/lib/types.ts` | Modify | Add `InputField`, update `WorkflowConfig`, `RunDetail` |
| `frontend/lib/api/workflows.ts` | Modify | Accept input in `triggerWorkflow()` |
| `frontend/app/workflows/page.tsx` | Modify | Dynamic input form modal |
| `frontend/app/components/WorkflowRunDetail.tsx` | Modify | Show input values |
| `backend/app/workflow/sample_workflow.py` | Modify | Demo input fields usage |

---

## Backward Compatibility

- `input_fields` defaults to `[]` — existing workflows work unchanged
- `input_data` defaults to `None` — existing trigger calls work unchanged
- `run(ctx)` is a **breaking change** for task subclasses — but since this is an early-stage project with only the sample workflow, this is acceptable. All existing task `run()` methods just need `ctx` added as a parameter (they can ignore it initially).

---

## Implementation Order

1. `InputField` + `BaseWorkflowConfig` update (backend foundation)
2. `BaseWorkflowContext` class (new file)
3. `BaseWorkflowTask.run()` signature change
4. DB migration + `WorkflowRun` model update
5. Orchestrator changes (validation, context creation, task execution)
6. API route updates (request body, response fields)
7. Frontend types + API client updates
8. Frontend input form modal
9. Frontend run detail input display
10. Sample workflow update

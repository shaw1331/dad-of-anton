# Workflow Inputs - Task Breakdown

## Epic: Variable Workflow Inputs

---

### TASK-017: Add `InputField` dataclass and update `BaseWorkflowConfig`

**File:** `backend/app/workflow/workflow_config.py`

**Description:**
Add an `InputField` dataclass to define workflow input fields, and add an `input_fields` list to `BaseWorkflowConfig`.

**Implementation:**
- Create `InputField` dataclass with fields: `name` (str), `type` (str), `label` (str), `description` (str, default ""), `required` (bool, default True), `default` (Any, default None)
- Add `input_fields: list[InputField] = field(default_factory=list)` to `BaseWorkflowConfig`
- Import `Any` from `typing`

**Acceptance Criteria:**
- [ ] `InputField` dataclass created with correct fields and defaults
- [ ] `BaseWorkflowConfig` has `input_fields` field defaulting to `[]`
- [ ] Existing workflow registrations (sample) still work without changes
- [ ] No import errors

---

### TASK-018: Create `BaseWorkflowContext` class

**New file:** `backend/app/workflow/base_workflow_context.py`

**Description:**
Create a `BaseWorkflowContext` class that holds input data and provides a mechanism for task outputs.

**Implementation:**
- `__init__(self, input: dict[str, Any])` — stores input dict
- `get_input(self, key: str) -> Any` — retrieves a value from input
- `set_output(self, task_name: str, value: Any) -> None` — stores task output
- `get_output(self, task_name: str) -> Any` — retrieves task output
- `_outputs: dict[str, Any]` — internal storage for task outputs

**Acceptance Criteria:**
- [ ] File created at `backend/app/workflow/base_workflow_context.py`
- [ ] `BaseWorkflowContext` can be instantiated with an input dict
- [ ] `get_input()` returns values from the input dict
- [ ] `set_output()` / `get_output()` work correctly
- [ ] No circular imports

---

### TASK-019: Update `BaseWorkflowTask.run()` signature

**File:** `backend/app/workflow/workflow_task.py`

**Description:**
Update the abstract `run()` method to accept a `BaseWorkflowContext` parameter.

**Implementation:**
- Import `BaseWorkflowContext` (use `TYPE_CHECKING` to avoid circular imports if needed)
- Change `async def run(self) -> None` to `async def run(self, ctx: BaseWorkflowContext) -> None`

**Acceptance Criteria:**
- [ ] `run()` method accepts `ctx: BaseWorkflowContext` parameter
- [ ] Class is still abstract
- [ ] No circular import issues

---

### TASK-020: Create DB migration for `input` column

**New file:** `backend/supabase/migrations/20260827000004_add_input_to_workflow_runs.sql`

**Description:**
Add a `input` JSONB column to the `workflow_runs` table to store workflow input data.

**Implementation:**
- `ALTER TABLE workflow_runs ADD COLUMN input jsonb;`
- Add a comment to the column for documentation

**Acceptance Criteria:**
- [ ] Migration file created
- [ ] `workflow_runs` table has `input` column of type `jsonb`
- [ ] Column is nullable (existing rows have NULL)
- [ ] Migration is idempotent or can be run safely

---

### TASK-021: Update `WorkflowRun` model

**File:** `backend/app/workflow/models/workflow_run.py`

**Description:**
Add `input` field to the `WorkflowRun` Pydantic model.

**Implementation:**
- Add `input: dict | None = None` field to `WorkflowRun`

**Acceptance Criteria:**
- [ ] `WorkflowRun` model has `input` field
- [ ] Field defaults to `None`
- [ ] `model_dump()` includes `input` (handles None correctly)
- [ ] `model_validate()` can parse existing DB rows (no `input` column → None)

---

### TASK-022: Update `BaseWorkflowOrchestrator` signature

**File:** `backend/app/workflow/base_workflow_orchestrator.py`

**Description:**
Update the `trigger_workflow` abstract method to accept optional input data.

**Implementation:**
- Change signature: `trigger_workflow(self, workflow_name: str, background_tasks: BackgroundTasks, input_data: dict | None = None) -> str`

**Acceptance Criteria:**
- [ ] `trigger_workflow` signature updated with `input_data` parameter
- [ ] Default value is `None`
- [ ] No other changes to the ABC

---

### TASK-023: Add input validation to `WorkflowOrchestrator`

**File:** `backend/app/workflow/workflow_orchestrator.py`

**Description:**
Add a `validate_input` method that validates user-provided input against the workflow's `input_fields` schema.

**Implementation:**
- Create `validate_input(self, config: BaseWorkflowConfig, input_data: dict) -> dict` method
- For each field in `config.input_fields`:
  - If field is in `input_data`: coerce to the declared type and store
  - If field is required and missing and no default: raise `ValueError`
  - If field has a default and is missing: use default
- Type coercion rules:
  - `str`: `str(value)`
  - `int`: `int(value)`
  - `float`: `float(value)`
  - `bool`: `str(value).lower() in ("true", "1", "yes")`
  - `text`: `str(value)`
- Return the validated/coerced dict

**Acceptance Criteria:**
- [ ] `validate_input` method exists on `WorkflowOrchestrator`
- [ ] Raises `ValueError` with clear message for missing required fields
- [ ] Coerces types correctly (str→int, str→float, etc.)
- [ ] Uses default values when field is missing and has a default
- [ ] Returns only validated fields (extra fields are ignored)

---

### TASK-024: Update `WorkflowOrchestrator.trigger_workflow()` to accept input

**File:** `backend/app/workflow/workflow_orchestrator.py`

**Description:**
Update `trigger_workflow` to accept, validate, and persist input data.

**Implementation:**
- Update method signature: add `input_data: dict | None = None`
- Call `self.validate_input(config, input_data or {})` — catch `ValueError` and re-raise
- Store validated input in `WorkflowRun` record: `input=validated_input`
- Pass validated input to `run_workflow` via DB (already done — `run_workflow` reads from DB)

**Acceptance Criteria:**
- [ ] `trigger_workflow` accepts `input_data` parameter
- [ ] Input is validated before creating DB records
- [ ] Invalid input raises an error with a clear message
- [ ] Validated input is stored in the `WorkflowRun` record
- [ ] Existing calls without `input_data` still work (defaults to `{}`)

---

### TASK-025: Update `WorkflowOrchestrator.run_workflow()` to create context and pass to tasks

**File:** `backend/app/workflow/workflow_orchestrator.py`

**Description:**
Update `run_workflow` to create a `BaseWorkflowContext` and pass it to each task's `run()` method.

**Implementation:**
- Import `BaseWorkflowContext`
- After fetching the run from DB, create context: `ctx = BaseWorkflowContext(input=run.input or {})`
- Change task execution: `await task_instance.run(ctx)` instead of `await task_instance.run()`
- Pass `ctx` to each task in the loop

**Acceptance Criteria:**
- [ ] `BaseWorkflowContext` is created with the run's input data
- [ ] Each task receives `ctx` as a parameter to `run()`
- [ ] Tasks can access input via `ctx.get_input("field_name")`
- [ ] Existing behavior preserved (tasks that don't use ctx still work)

---

### TASK-026: Update API trigger endpoint to accept input body

**File:** `backend/app/api/v1/workflow_routes.py`

**Description:**
Update the `POST /{name}/trigger` endpoint to accept a JSON body with input data.

**Implementation:**
- Create `TriggerRequest` Pydantic model: `input: dict[str, Any] = {}`
- Update `trigger_workflow` endpoint to accept `request: TriggerRequest` body parameter
- Pass `request.input` to `orchestrator.trigger_workflow(name, background_tasks, request.input)`
- Catch `ValueError` from validation and return 422 with error detail

**Acceptance Criteria:**
- [ ] Endpoint accepts POST body with `input` field
- [ ] Missing body defaults to empty input (`{}`)
- [ ] Validation errors return 422 with clear message
- [ ] Existing trigger calls without body still work

---

### TASK-027: Update API list endpoint to return `input_fields`

**File:** `backend/app/api/v1/workflow_routes.py`

**Description:**
Update `GET /workflows` to include `input_fields` in the response for each workflow.

**Implementation:**
- In `list_workflows()`, serialize `input_fields` from config
- Each field: `{"name": f.name, "type": f.type, "label": f.label, "description": f.description, "required": f.required, "default": f.default}`

**Acceptance Criteria:**
- [ ] Response includes `input_fields` array for each workflow
- [ ] Fields are serialized correctly (no dataclass objects in JSON)
- [ ] Workflows with no input_fields return empty array

---

### TASK-028: Update frontend TypeScript types

**File:** `frontend/lib/types.ts`

**Description:**
Add `InputField` interface and update existing types to include input-related fields.

**Implementation:**
- Add `InputField` interface: `{ name, type, label, description, required, default }`
- Update `WorkflowConfig` to include `input_fields: InputField[]`
- Update `RunDetail` to include `input: Record<string, any> | null`

**Acceptance Criteria:**
- [ ] `InputField` interface exists
- [ ] `WorkflowConfig` includes `input_fields`
- [ ] `RunDetail` includes `input`
- [ ] No TypeScript compilation errors

---

### TASK-029: Update frontend API client

**File:** `frontend/lib/api/workflows.ts`

**Description:**
Update `triggerWorkflow()` to accept and send input data.

**Implementation:**
- Change signature: `triggerWorkflow(workflowName: string, input?: Record<string, any>)`
- Send `JSON.stringify({ input: input ?? {} })` as body
- Set `Content-Type: application/json` header

**Acceptance Criteria:**
- [ ] `triggerWorkflow` accepts optional `input` parameter
- [ ] Input is sent as JSON body
- [ ] Calls without input still work

---

### TASK-030: Build dynamic input form modal on workflows page

**File:** `frontend/app/workflows/page.tsx`

**Description:**
When a workflow has `input_fields`, show a modal form before triggering. Workflows with no inputs trigger immediately.

**Implementation:**
- Add state: `selectedWorkflow: WorkflowConfig | null`, `showModal: boolean`, `formData: Record<string, any>`
- "Trigger" button logic:
  - If `workflow.input_fields.length === 0`: trigger immediately (existing behavior)
  - If `workflow.input_fields.length > 0`: set `selectedWorkflow`, open modal
- Modal rendering:
  - For each `input_field`, render appropriate input:
    - `type: "str"` → `<input type="text">`
    - `type: "int"` → `<input type="number" step="1">`
    - `type: "float"` → `<input type="number" step="0.01">`
    - `type: "bool"` → `<input type="checkbox">`
    - `type: "text"` → `<textarea>`
  - Show `label` as field label, `description` as help text
  - Mark required fields with `*`
  - Pre-fill `default` values
- Modal actions:
  - "Trigger": validate required fields client-side, call `triggerWorkflow(name, formData)`, close modal
  - "Cancel": close modal, reset form

**Acceptance Criteria:**
- [ ] Workflows with no inputs trigger immediately (no regression)
- [ ] Workflows with inputs open a modal on "Trigger" click
- [ ] Modal renders correct input types based on `input_fields`
- [ ] Required fields are marked and validated
- [ ] Default values are pre-filled
- [ ] Form submission triggers the workflow with input data
- [ ] Modal can be cancelled/closed

---

### TASK-031: Show input values in run detail view

**File:** `frontend/app/components/WorkflowRunDetail.tsx`

**Description:**
Display the workflow's input values in the run detail view.

**Implementation:**
- Add an "Input" section above the task list
- Render input as key-value pairs in a small info card
- Only show if `run.input` is non-null and has keys
- Style consistently with existing components

**Acceptance Criteria:**
- [ ] Input section appears in run detail when input exists
- [ ] Input is displayed as key-value pairs
- [ ] Section is hidden when no input is present
- [ ] Styled consistently with the rest of the detail view

---

### TASK-032: Update sample workflow with input fields

**File:** `backend/app/workflow/sample_workflow.py`

**Description:**
Update the sample workflow to demonstrate input usage.

**Implementation:**
- Add `InputField(name="message", type="str", label="Message", description="Message to print", required=False, default="Hello from task!")` to sample config
- Update `PrintMessageTask.run()` to accept `ctx: BaseWorkflowContext` and use `ctx.get_input("message")` if available, falling back to `self.message`
- Import `BaseWorkflowContext` and `InputField`

**Acceptance Criteria:**
- [ ] Sample workflow has `input_fields` defined
- [ ] `PrintMessageTask.run()` accepts `ctx` parameter
- [ ] Task uses input from context when available
- [ ] Workflow still works when triggered without input (uses default)
- [ ] Workflow works when triggered with custom input

---

### TASK-033: End-to-end integration test for inputs

**Description:**
Manually test the full input flow end-to-end.

**Steps:**
1. Start backend and frontend servers
2. Navigate to `/workflows`
3. Verify sample workflow shows input form on "Trigger"
4. Submit form with custom message
5. Verify run detail shows the input value
6. Verify task printed the custom message
7. Trigger sample workflow without filling form (use default)
8. Verify it uses the default message
9. Test validation: remove a required field, verify error message

**Acceptance Criteria:**
- [ ] Input form appears for workflows with input_fields
- [ ] Custom input is passed to the workflow
- [ ] Input is displayed in run detail
- [ ] Default values work when input is not provided
- [ ] Validation errors are shown for missing required fields
- [ ] Existing workflows without inputs still trigger normally

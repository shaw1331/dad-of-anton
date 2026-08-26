# Workflow Orchestrator - Task Breakdown

## Epic: Workflow Orchestrator

---

### TASK-001: Create Supabase `workflow_runs` table

**Description:**
Create the `workflow_runs` table in Supabase to track each workflow execution. Use Supabase SQL editor or dashboard.

**Columns:**
- `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
- `workflow_name` text NOT NULL
- `status` text NOT NULL DEFAULT 'pending' (enum-like: pending, running, completed, failed)
- `current_task_index` int NOT NULL DEFAULT 0
- `total_tasks` int NOT NULL
- `error` text
- `created_at` timestamptz NOT NULL DEFAULT now()
- `updated_at` timestamptz NOT NULL DEFAULT now()

**Acceptance Criteria:**
- [x] Table created in Supabase
- [x] RLS policies set (allow all for now, or restrict as needed)
- [x] `updated_at` auto-updates via trigger

---

### TASK-002: Create Supabase `workflow_task_runs` table

**Description:**
Create the `workflow_task_runs` table in Supabase to track individual task execution within a workflow run.

**Columns:**
- `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
- `workflow_run_id` uuid NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE
- `task_name` text NOT NULL
- `task_index` int NOT NULL
- `status` text NOT NULL DEFAULT 'pending' (enum-like: pending, running, completed, failed)
- `error` text
- `started_at` timestamptz
- `completed_at` timestamptz
- `created_at` timestamptz NOT NULL DEFAULT now()

**Acceptance Criteria:**
- [x] Table created in Supabase
- [x] Foreign key to `workflow_runs` with ON DELETE CASCADE
- [x] RLS policies set

---

### TASK-003: Create `BaseWorkflowTask` abstract base class

**Description:**
Create the `backend/app/workflow/workflow_task.py` file with the abstract base class for all workflow tasks.

**Implementation:**
- Abstract class `BaseWorkflowTask` with ABC
- Abstract method `async def run(self) -> None`
- `name` class attribute (str) for human-readable task name

**Acceptance Criteria:**
- [x] File created at `backend/app/workflow/workflow_task.py`
- [x] Class is abstract (cannot be instantiated directly)
- [x] `run()` method is async and raises NotImplementedError if not overridden

---

### TASK-004: Create `BaseWorkflowConfig` dataclass

**Description:**
Create the `backend/app/workflow/workflow_config.py` file with the dataclass for workflow configuration and the workflow registry.

**Implementation:**
- `BaseWorkflowConfig` dataclass with fields: `name`, `description`, `tasks` (list of task classes)
- `WORKFLOWS` dictionary to register workflow configs by name

**Acceptance Criteria:**
- [x] File created at `backend/app/workflow/workflow_config.py`
- [x] `BaseWorkflowConfig` is a dataclass
- [x] `WORKFLOWS` is a module-level dict
- [x] Type hints are correct

---

### TASK-005: Create `WorkflowOrchestrator` class

**Description:**
Create the `BaseWorkflowOrchestrator` abstract base class and `WorkflowOrchestrator` implementation with the core orchestration logic.

**Implementation:**
- `BaseWorkflowOrchestrator` ABC in `backend/app/workflow/base_workflow_orchestrator.py` with abstract methods: `resolve_config`, `trigger_workflow`, `run_workflow`
- `WorkflowOrchestrator` in `backend/app/workflow/workflow_orchestrator.py` implementing the dict-registry based orchestrator
- `trigger_workflow(workflow_name: str, background_tasks: BackgroundTasks) -> str`: Creates workflow_run + task_run records in DB, kicks off background task, returns run_id
- `run_workflow(run_id: str)`: Iterates through tasks, updates DB status, catches exceptions
- `resolve_config(workflow_name) -> BaseWorkflowConfig`: Resolves workflow config from registry
- `resolve_task_name(task_cls)` helper for task name resolution
- Uses repository classes for DB operations
- Uses FastAPI `BackgroundTasks` for async execution

**Acceptance Criteria:**
- [x] `base_workflow_orchestrator.py` created with `BaseWorkflowOrchestrator` ABC
- [x] `workflow_orchestrator.py` created with `WorkflowOrchestrator` implementation
- [x] `trigger_workflow` creates DB records and kicks off background task
- [x] `run_workflow` updates status at each step (pending -> running -> completed/failed)
- [x] Error handling: if a task fails, workflow status becomes 'failed' with error message
- [x] `current_task_index` is updated as tasks progress
- [x] Future extensible via `BaseWorkflowOrchestrator` base class

---

### TASK-006: Create workflow module `__init__.py`

**Description:**
Create `backend/app/workflow/__init__.py` to export the public API of the workflow module.

**Exports:**
- `BaseWorkflowTask`
- `BaseWorkflowConfig`
- `WORKFLOWS`
- `trigger_workflow`

**Acceptance Criteria:**
- [x] File created at `backend/app/workflow/__init__.py`
- [x] All public symbols are importable from `app.workflow`

---

### TASK-007: Create workflow API router

**Description:**
Create `backend/app/api/v1/workflow_routes.py` with FastAPI endpoints for workflow management.

**Endpoints:**
- `GET /workflows` - List all registered workflow configs from `WORKFLOWS` dict
- `POST /workflows/{name}/trigger` - Trigger a new workflow run, returns run_id
- `GET /workflows/runs` - List all workflow runs from DB
- `GET /workflows/runs/{run_id}` - Get a single run with its task_runs

**Acceptance Criteria:**
- [ ] File created at `backend/app/api/v1/workflow_routes.py`
- [ ] Router uses `APIRouter` with appropriate prefix/tags
- [ ] All endpoints return proper JSON responses
- [ ] Error handling for non-existent workflow names
- [ ] Error handling for non-existent run_ids

---

### TASK-008: Register workflow router in main API

**Description:**
Update `backend/app/api/v1/__init__.py` to include the new workflow router.

**Implementation:**
- Import the workflow router from `workflow_routes.py`
- Include it in the `api_router`

**Acceptance Criteria:**
- [ ] Workflow endpoints are accessible at `/api/v1/workflows/...`
- [ ] Existing `/health` endpoint still works
- [ ] No import errors

---

### TASK-009: Create sample workflow for testing

**Description:**
Create a sample workflow with 2-3 dummy tasks to verify the end-to-end flow.

**Implementation:**
- Create `backend/app/workflow/sample_workflow.py`
- Define 2-3 simple tasks (e.g., print message, sleep, print another message)
- Register the workflow in `WORKFLOWS`

**Acceptance Criteria:**
- [ ] Sample workflow file created
- [ ] Tasks inherit from `BaseWorkflowTask`
- [ ] Workflow is registered in `WORKFLOWS`
- [ ] Can trigger via API and see tasks execute in sequence

---

### TASK-010: Frontend - Create workflows list page

**Description:**
Create `frontend/app/workflows/page.tsx` to display all registered workflows and recent runs.

**Implementation:**
- Fetch workflow configs from `GET /api/v1/workflows`
- Fetch recent runs from `GET /api/v1/workflows/runs`
- Display workflows with "Trigger" button
- Display runs with status badges

**Acceptance Criteria:**
- [ ] Page created at `frontend/app/workflows/page.tsx`
- [ ] Lists all registered workflows
- [ ] "Trigger" button calls POST endpoint and refreshes list
- [ ] Shows recent runs with status (pending/running/completed/failed)
- [ ] Clicking a run navigates to detail page

---

### TASK-011: Frontend - Create workflow run detail page

**Description:**
Create `frontend/app/workflows/[runId]/page.tsx` to show detailed status of a single workflow run.

**Implementation:**
- Fetch run details from `GET /api/v1/workflows/runs/{runId}`
- Display workflow name, overall status, progress (current step / total)
- List all tasks with individual status, start/end times

**Acceptance Criteria:**
- [ ] Page created at `frontend/app/workflows/[runId]/page.tsx`
- [ ] Shows workflow name and overall status
- [ ] Shows progress bar or step indicator (e.g., "Step 3/7")
- [ ] Lists tasks with status badges
- [ ] Auto-refreshes or polls for status updates

---

### TASK-012: Frontend - Create `WorkflowList` component

**Description:**
Create `frontend/app/components/WorkflowList.tsx` to display the list of registered workflow configs.

**Props:**
- `workflows`: Array of workflow config objects
- `onTrigger`: Callback when trigger button is clicked

**Acceptance Criteria:**
- [ ] Component created at `frontend/app/components/WorkflowList.tsx`
- [ ] Displays workflow name and description
- [ ] Has a "Trigger" button per workflow
- [ ] Accepts props for data and callbacks

---

### TASK-013: Frontend - Create `WorkflowRunList` component

**Description:**
Create `frontend/app/components/WorkflowRunList.tsx` to display recent workflow runs.

**Props:**
- `runs`: Array of workflow run objects
- `onSelect`: Callback when a run is clicked

**Acceptance Criteria:**
- [ ] Component created at `frontend/app/components/WorkflowRunList.tsx`
- [ ] Displays run ID, workflow name, status, created time
- [ ] Status shown as colored badge (green=completed, red=failed, yellow=running, gray=pending)
- [ ] Clicking a run calls `onSelect` with the run_id

---

### TASK-014: Frontend - Create `WorkflowRunDetail` component

**Description:**
Create `frontend/app/components/WorkflowRunDetail.tsx` to display detailed task progress for a single run.

**Props:**
- `run`: Workflow run object with nested task_runs

**Acceptance Criteria:**
- [ ] Component created at `frontend/app/components/WorkflowRunDetail.tsx`
- [ ] Shows workflow name and overall status
- [ ] Lists each task with name, status, start/end times
- [ ] Current/running task is highlighted
- [ ] Progress indicator shows step number

---

### TASK-015: Frontend - Add workflow navigation link

**Description:**
Update the home page or add navigation to access the workflows page.

**Implementation:**
- Add a link to `/workflows` from the home page

**Acceptance Criteria:**
- [ ] User can navigate to workflows page from home page
- [ ] Navigation is intuitive

---

### TASK-016: End-to-end integration test

**Description:**
Manually test the full flow from triggering a workflow via UI to seeing it complete.

**Steps:**
1. Start backend server
2. Start frontend dev server
3. Navigate to `/workflows`
4. Click "Trigger" on the sample workflow
5. Verify run appears in the runs list
6. Click on the run to see detail page
7. Verify tasks show correct status progression

**Acceptance Criteria:**
- [ ] Can trigger workflow from UI
- [ ] Run appears in list immediately with 'pending' status
- [ ] Detail page shows task progress
- [ ] Workflow completes successfully (all tasks show 'completed')
- [ ] Error case: if a task fails, status shows 'failed' with error message

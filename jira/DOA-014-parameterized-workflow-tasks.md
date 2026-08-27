# DOA-014: Workflow configs can't parameterize tasks (and the sample workflow blocks for 60 s)

- **Type:** Improvement (design gap)
- **Priority:** P1
- **Component:** backend / workflow
- **Affected files:** `backend/app/workflow/workflow_config.py`, `backend/app/workflow/workflow_orchestrator.py`, `backend/app/workflow/sample_workflow.py`

## Problem

1. **Task constructor arguments are unusable.** `BaseWorkflowConfig.tasks` is `list[type[BaseWorkflowTask]]` (classes, not instances), and the orchestrator instantiates them with **no arguments** (`workflow_orchestrator.py:69`: `task_instance = task_cls()`). Yet the sample tasks define rich constructors:

   ```python
   class PrintMessageTask(BaseWorkflowTask):
       def __init__(self, message: str = "Hello from task!") -> None: ...

   class DelayTask(BaseWorkflowTask):
       def __init__(self, seconds: float = 60.0) -> None: ...
   ```

   There is no way for a workflow definition to say `PrintMessageTask("step 2")` or `DelayTask(5)` — the constructor params are dead API. Any real workflow will need per-step configuration on day one.

2. **The sample workflow sleeps 60 seconds.** `DelayTask` defaults to `60.0`, so every smoke-test of `POST /workflows/sample/trigger` occupies the runner for a minute (and, until DOA-005 lands, all those DB status writes interleave with a long-lived background task). A demo flow should complete in seconds.

## Fix

Hold **task instances** in the config instead of classes. Tasks in this codebase are stateless between runs (state lives in `workflow_task_runs`), so reusing one instance across runs is safe and makes configs read naturally:

```python
tasks=[PrintMessageTask("starting"), DelayTask(2.0), PrintMessageTask("done")]
```

`resolve_task_name` shifts from class attributes to instance attributes.

## Steps of completion

1. Change `BaseWorkflowConfig.tasks` to `list[BaseWorkflowTask]`.
2. Update `resolve_task_name` to accept an instance; update both loops in the orchestrator to use the instance directly (no `task_cls()` call).
3. Update `sample_workflow.py` to register instances with explicit, fast parameters (delay 2 s).
4. Add a docstring note on `BaseWorkflowTask` that instances must be safe to `run()` multiple times.
5. Trigger `sample`: it must complete in ~2 s, printing the two distinct messages.

## Changes (diff)

### `backend/app/workflow/workflow_config.py`

```diff
@@ -8,6 +8,6 @@
 @dataclass
 class BaseWorkflowConfig:
     name: str
     description: str
-    tasks: list[type[BaseWorkflowTask]] = field(default_factory=list)
+    tasks: list[BaseWorkflowTask] = field(default_factory=list)
```

### `backend/app/workflow/workflow_orchestrator.py`

```diff
@@ -16,8 +16,8 @@
-def resolve_task_name(task_cls: type) -> str:
-    return task_cls.name if hasattr(task_cls, "name") else task_cls.__name__
+def resolve_task_name(task: "BaseWorkflowTask") -> str:
+    return getattr(task, "name", None) or type(task).__name__
@@ -42,9 +42,9 @@
-        for index, task_cls in enumerate(config.tasks):
+        for index, task in enumerate(config.tasks):
             task_run = WorkflowTaskRun(
                 workflow_run_id=run.id,
-                task_name=resolve_task_name(task_cls),
+                task_name=resolve_task_name(task),
                 task_index=index,
                 status="pending",
             )
@@ -61,20 +61,19 @@
         try:
-            for index, task_cls in enumerate(config.tasks):
+            for index, task in enumerate(config.tasks):
                 self.run_repo.update_progress(run_id, index)

                 task_run = self.task_run_repo.get(run_id, index)
                 self.task_run_repo.update_running(task_run.id)

                 try:
-                    task_instance = task_cls()
-                    await task_instance.run()
+                    await task.run()

                     self.task_run_repo.update_status(task_run.id, "completed")
                 except Exception as e:
-                    task_name = resolve_task_name(task_cls)
+                    task_name = resolve_task_name(task)
                     logger.error("Task %s failed: %s", task_name, e)
```

*(Import of `BaseWorkflowTask` for the type hint: add `from app.workflow.workflow_task import BaseWorkflowTask` to the imports, or keep the string annotation as shown.)*

### `backend/app/workflow/sample_workflow.py`

```diff
@@ -28,8 +28,12 @@
 WORKFLOWS["sample"] = BaseWorkflowConfig(
     name="sample",
     description="A sample workflow with 3 dummy tasks",
-    tasks=[PrintMessageTask, DelayTask, PrintMessageTask],
+    tasks=[
+        PrintMessageTask("sample workflow: starting"),
+        DelayTask(2.0),
+        PrintMessageTask("sample workflow: done"),
+    ],
 )
```

### `backend/app/workflow/workflow_task.py`

```diff
@@ -1,9 +1,13 @@
 from abc import ABC, abstractmethod


 class BaseWorkflowTask(ABC):
+    """A single step in a workflow.
+
+    Instances are registered once in a workflow config and re-run for every
+    workflow run — `run()` must be safe to call multiple times and must not
+    keep per-run state on `self`.
+    """
     name: str

     @abstractmethod
     async def run(self) -> None:
         pass
```

> Interaction with other tickets: DOA-005 wraps the surrounding repo calls in `run_in_threadpool` and DOA-003 swaps status strings for enums — all three touch the same loop. Recommended landing order: DOA-006 → DOA-014 → DOA-005 → DOA-003 (or a single combined PR).

## Acceptance criteria

- [ ] `POST /api/v1/workflows/sample/trigger` completes in < 5 s with distinct log messages per print task.
- [ ] A config with two differently-parameterized instances of the same class records both task rows with correct names and runs both.
- [ ] `GET /api/v1/workflows` still reports `task_count: 3` for `sample` (route code unchanged — `len(config.tasks)` works on instances).

from __future__ import annotations

import asyncio
import logging

from fastapi import BackgroundTasks

from app.workflow.base_workflow_context import BaseWorkflowContext
from app.workflow.base_workflow_orchestrator import BaseWorkflowOrchestrator
from app.workflow.models import WorkflowRun, WorkflowTaskRun
from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository
from app.workflow.base_workflow_config import BaseWorkflowConfig
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

logger = logging.getLogger(__name__)


def resolve_task_name(task_cls: type) -> str:
    return task_cls.name if hasattr(task_cls, "name") else task_cls.__name__


def _coerce_type(value: object, field_type: str) -> object:
    if field_type == "str":
        return str(value)
    elif field_type == "int":
        return int(value)
    elif field_type == "float":
        return float(value)
    elif field_type == "bool":
        return str(value).lower() in ("true", "1", "yes")
    elif field_type == "text":
        return str(value)
    return value


class WorkflowOrchestrator(BaseWorkflowOrchestrator):
    def __init__(self) -> None:
        self.run_repo = WorkflowRunRepository()
        self.task_run_repo = WorkflowTaskRunRepository()

    def resolve_config(self, workflow_name: str) -> BaseWorkflowConfig:
        config = WORKFLOWS.get(workflow_name)
        if config is None:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        return config

    def validate_input(self, config: BaseWorkflowConfig, input_data: dict) -> dict:
        validated: dict = {}
        for field in config.input_fields:
            if field.name in input_data:
                validated[field.name] = _coerce_type(input_data[field.name], field.type)
            elif field.required and field.default is None:
                raise ValueError(f"Missing required field: {field.name}")
            elif field.default is not None:
                validated[field.name] = field.default
        return validated

    def trigger_workflow(
        self, workflow_name: str, background_tasks: BackgroundTasks, input_data: dict | None = None
    ) -> str:
        config = self.resolve_config(workflow_name)
        validated_input = self.validate_input(config, input_data or {})

        run = WorkflowRun(
            workflow_name=workflow_name,
            status="pending",
            current_task_index=0,
            total_tasks=len(config.tasks),
            input=validated_input,
        )
        self.run_repo.create(run)

        for index, task_cls in enumerate(config.tasks):
            task_run = WorkflowTaskRun(
                workflow_run_id=run.id,
                task_name=resolve_task_name(task_cls),
                task_index=index,
                status="pending",
            )
            self.task_run_repo.create(task_run)

        background_tasks.add_task(self.run_workflow, run.id)

        return run.id

    async def run_workflow(self, run_id: str) -> None:
        await asyncio.to_thread(self.run_repo.update_status, run_id, "running")

        run = await asyncio.to_thread(self.run_repo.get, run_id)
        config = self.resolve_config(run.workflow_name)
        ctx = BaseWorkflowContext(input=run.input or {})

        try:
            for index, task_cls in enumerate(config.tasks):
                await asyncio.to_thread(self.run_repo.update_progress, run_id, index)

                task_run = await asyncio.to_thread(self.task_run_repo.get, run_id, index)
                await asyncio.to_thread(self.task_run_repo.update_running, task_run.id)

                task_name = resolve_task_name(task_cls)
                try:
                    task_instance = task_cls()
                    await asyncio.to_thread(task_instance.run, ctx)

                    task_output = ctx.get_output(task_name)
                    if task_output is not None:
                        await asyncio.to_thread(self.task_run_repo.update_output, task_run.id, task_output)

                    await asyncio.to_thread(self.task_run_repo.update_status, task_run.id, "completed")
                except Exception as e:
                    logger.error("Task %s failed: %s", task_name, e)
                    await asyncio.to_thread(self.task_run_repo.update_status, task_run.id, "failed", str(e))
                    await asyncio.to_thread(
                        self.run_repo.update_status,
                        run_id,
                        "failed",
                        f"Task '{task_name}' failed: {e}",
                    )
                    return

            await asyncio.to_thread(self.run_repo.update_status, run_id, "completed")

            final_task_name = resolve_task_name(config.tasks[-1])
            final_output = ctx.get_output(final_task_name)
            if final_output is not None:
                await asyncio.to_thread(self.run_repo.update_output, run_id, final_output)
        except Exception as e:
            logger.error("Workflow %s failed unexpectedly: %s", run_id, e)
            await asyncio.to_thread(self.run_repo.update_status, run_id, "failed", f"Unexpected error: {e}")


orchestrator = WorkflowOrchestrator()

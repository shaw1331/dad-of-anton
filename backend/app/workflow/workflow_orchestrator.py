from __future__ import annotations

import asyncio
import logging

from fastapi import BackgroundTasks

from app.workflow.base_workflow_orchestrator import BaseWorkflowOrchestrator
from app.workflow.models import WorkflowRun, WorkflowTaskRun
from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository
from app.workflow.workflow_config import BaseWorkflowConfig
from app.workflow.workflow_registry import WORKFLOWS

logger = logging.getLogger(__name__)


def resolve_task_name(task_cls: type) -> str:
    return task_cls.name if hasattr(task_cls, "name") else task_cls.__name__


class WorkflowOrchestrator(BaseWorkflowOrchestrator):
    def __init__(self) -> None:
        self.run_repo = WorkflowRunRepository()
        self.task_run_repo = WorkflowTaskRunRepository()

    def resolve_config(self, workflow_name: str) -> BaseWorkflowConfig:
        config = WORKFLOWS.get(workflow_name)
        if config is None:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        return config

    def trigger_workflow(self, workflow_name: str, background_tasks: BackgroundTasks) -> str:
        config = self.resolve_config(workflow_name)

        run = WorkflowRun(
            workflow_name=workflow_name,
            status="pending",
            current_task_index=0,
            total_tasks=len(config.tasks),
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

    def run_workflow(self, run_id: str) -> None:
        self.run_repo.update_status(run_id, "running")

        run = self.run_repo.get(run_id)
        config = self.resolve_config(run.workflow_name)

        try:
            for index, task_cls in enumerate(config.tasks):
                self.run_repo.update_progress(run_id, index)

                task_run = self.task_run_repo.get(run_id, index)
                self.task_run_repo.update_running(task_run.id)

                try:
                    task_instance = task_cls()
                    asyncio.run(task_instance.run())

                    self.task_run_repo.update_status(task_run.id, "completed")
                except Exception as e:
                    task_name = resolve_task_name(task_cls)
                    logger.error("Task %s failed: %s", task_name, e)
                    self.task_run_repo.update_status(task_run.id, "failed", str(e))
                    self.run_repo.update_status(
                        run_id,
                        "failed",
                        f"Task '{task_name}' failed: {e}",
                    )
                    return

            self.run_repo.update_status(run_id, "completed")
        except Exception as e:
            logger.error("Workflow %s failed unexpectedly: %s", run_id, e)
            self.run_repo.update_status(run_id, "failed", f"Unexpected error: {e}")


orchestrator = WorkflowOrchestrator()

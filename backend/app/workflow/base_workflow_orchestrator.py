from __future__ import annotations

from abc import ABC, abstractmethod

from fastapi import BackgroundTasks

from app.workflow.base_workflow_config import BaseWorkflowConfig


class BaseWorkflowOrchestrator(ABC):
    @abstractmethod
    def resolve_config(self, workflow_name: str) -> BaseWorkflowConfig:
        ...

    @abstractmethod
    def trigger_workflow(self, workflow_name: str, background_tasks: BackgroundTasks) -> str:
        ...

    @abstractmethod
    def run_workflow(self, run_id: str) -> None:
        ...

from __future__ import annotations

from dataclasses import dataclass, field

from app.workflow.base_workflow_task import BaseWorkflowTask


@dataclass
class BaseWorkflowConfig:
    name: str
    description: str
    tasks: list[type[BaseWorkflowTask]] = field(default_factory=list)

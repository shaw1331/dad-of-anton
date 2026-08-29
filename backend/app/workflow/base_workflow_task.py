from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.workflow.base_workflow_context import BaseWorkflowContext


class BaseWorkflowTask(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: BaseWorkflowContext) -> None:
        pass

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.workflow.base_workflow_config import BaseWorkflowConfig
from app.workflow.base_workflow_task import BaseWorkflowTask
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

if TYPE_CHECKING:
    from app.workflow.base_workflow_context import BaseWorkflowContext


class PrintMessageTask(BaseWorkflowTask):
    name = "print_message"

    def __init__(self, message: str = "Hello from task!") -> None:
        self.message = message

    async def run(self, ctx: BaseWorkflowContext) -> None:
        print(self.message)


class DelayTask(BaseWorkflowTask):
    name = "delay"

    def __init__(self, seconds: float = 60.0) -> None:
        self.seconds = seconds

    async def run(self, ctx: BaseWorkflowContext) -> None:
        await asyncio.sleep(self.seconds)


WORKFLOWS["sample"] = BaseWorkflowConfig(
    name="sample",
    description="A sample workflow with 3 dummy tasks",
    tasks=[PrintMessageTask, DelayTask, PrintMessageTask],
)

from __future__ import annotations

import asyncio

from app.workflow.workflow_config import BaseWorkflowConfig
from app.workflow.workflow_registry import WORKFLOWS
from app.workflow.workflow_task import BaseWorkflowTask


class PrintMessageTask(BaseWorkflowTask):
    name = "print_message"

    def __init__(self, message: str = "Hello from task!") -> None:
        self.message = message

    async def run(self) -> None:
        print(self.message)


class DelayTask(BaseWorkflowTask):
    name = "delay"

    def __init__(self, seconds: float = 60.0) -> None:
        self.seconds = seconds

    async def run(self) -> None:
        await asyncio.sleep(self.seconds)


WORKFLOWS["sample"] = BaseWorkflowConfig(
    name="sample",
    description="A sample workflow with 3 dummy tasks",
    tasks=[PrintMessageTask, DelayTask, PrintMessageTask],
)

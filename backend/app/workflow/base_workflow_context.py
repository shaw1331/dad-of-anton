from typing import Any


class BaseWorkflowContext:
    def __init__(self, input: dict[str, Any]) -> None:
        self.input = input
        self._outputs: dict[str, Any] = {}

    def get_input(self, key: str) -> Any:
        return self.input.get(key)

    def set_output(self, task_name: str, value: Any) -> None:
        self._outputs[task_name] = value

    def get_output(self, task_name: str) -> Any:
        return self._outputs.get(task_name)

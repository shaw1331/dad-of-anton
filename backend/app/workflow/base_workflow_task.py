from abc import ABC, abstractmethod


class BaseWorkflowTask(ABC):
    name: str

    @abstractmethod
    async def run(self) -> None:
        pass

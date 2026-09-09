from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.workflow.base_workflow_task import BaseWorkflowTask


InputFieldType = Literal["str", "int", "float", "bool", "text", "ticker"]


@dataclass
class InputField:
    name: str
    type: InputFieldType
    label: str
    description: str = ""
    required: bool = True
    default: Any = None
    choices: list[str] | None = None


@dataclass
class BaseWorkflowConfig:
    name: str
    description: str
    tasks: list[type[BaseWorkflowTask]] = field(default_factory=list)
    input_fields: list[InputField] = field(default_factory=list)

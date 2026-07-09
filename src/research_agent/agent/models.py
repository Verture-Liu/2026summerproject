from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InputRef(StrictModel):
    source: Literal["uploaded", "step"]
    ref: str = Field(min_length=1)


class OutputSpec(StrictModel):
    name: str = Field(min_length=1)
    format: str = Field(min_length=1)


class WorkflowStep(StrictModel):
    id: str = Field(pattern=r"^step_[0-9]{2,}$")
    skill: str = Field(min_length=1)
    inputs: list[InputRef]
    parameters: dict[str, Any] = Field(default_factory=dict)
    outputs: list[OutputSpec]
    reason: str = Field(min_length=1)


class Workflow(StrictModel):
    schema_version: Literal["1.0"]
    task_summary: str = Field(min_length=1)
    steps: list[WorkflowStep] = Field(min_length=1)

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class SkillContext:
    work_dir: Path
    inputs: list[Path]

    def __post_init__(self):
        object.__setattr__(self, "work_dir", Path(self.work_dir).resolve())
        object.__setattr__(
            self,
            "inputs",
            [Path(path).resolve() for path in self.inputs],
        )


@dataclass(frozen=True)
class SkillResult:
    status: str
    outputs: list[str]
    metrics: dict[str, Any]
    warnings: list[str]
    error: str | None = None


class Skill(Protocol):
    name: str
    description: str
    input_formats: set[str]
    output_formats: set[str]
    resource_class: str
    parameter_schema: dict[str, Any]

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        ...

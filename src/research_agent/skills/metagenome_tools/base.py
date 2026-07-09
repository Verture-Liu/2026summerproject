from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from research_agent.skills.ancient_dna.common import run_command, write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import ToolCommand, resolve_tool


class LocalCliSkill(ABC):
    resource_class = "heavy"
    timeout_seconds = 24 * 3600
    executable_candidates: tuple[str, ...]
    official_url: str
    installation_hint: str

    def find_tool_command(self) -> ToolCommand | None:
        return resolve_tool(self.executable_candidates)

    def find_executable(self) -> str | None:
        tool_command = self.find_tool_command()
        return tool_command.command[-1] if tool_command else None

    @abstractmethod
    def build_command(
        self, context: SkillContext, parameters: dict, executable: str
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def output_roots(
        self, context: SkillContext, parameters: dict
    ) -> list[Path]:
        raise NotImplementedError

    def _collect_outputs(
        self, context: SkillContext, parameters: dict
    ) -> list[Path]:
        outputs: list[Path] = []
        for root in self.output_roots(context, parameters):
            if root.is_file():
                outputs.append(root)
            elif root.is_dir():
                outputs.extend(
                    sorted(path for path in root.rglob("*") if path.is_file())
                )
        return outputs

    def prepare_directories(
        self, context: SkillContext, parameters: dict
    ) -> list[Path]:
        return []

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = self.find_tool_command()
        report = {
            "ready": tool_command is not None,
            "tool": self.executable_candidates[0],
            "executable": " ".join(tool_command.command) if tool_command else "",
            "source": tool_command.source if tool_command else "",
            "official_url": self.official_url,
            "installation_instructions": [
                self.installation_hint,
                (
                    "Install the tool and required databases in a dedicated "
                    "environment, then restart the Agent."
                ),
                "The Agent will not install external software automatically.",
            ],
        }
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"dependency_report": report},
                [],
                (
                    f"Required tool is missing: {self.executable_candidates[0]}. "
                    + " ".join(report["installation_instructions"])
                ),
            )
        try:
            for source in context.inputs:
                if not source.exists():
                    raise ValueError(f"Input does not exist: {source}")
            context.work_dir.mkdir(parents=True, exist_ok=True)
            for directory in self.prepare_directories(context, parameters):
                directory.mkdir(parents=True, exist_ok=True)
            command = self.build_command(context, parameters, tool_command.tool)
            if command and command[0] == tool_command.tool:
                command = [*tool_command.command, *command[1:]]
            completed = run_command(
                command,
                cwd=context.work_dir,
                stdout_path=context.work_dir / f"{self.name}_stdout.log",
                stderr_path=context.work_dir / f"{self.name}_stderr.log",
                timeout=self.timeout_seconds,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"{self.executable_candidates[0]} exited with code "
                    f"{completed.returncode}: {completed.stderr.strip()}"
                )
            outputs = self._collect_outputs(context, parameters)
            if not outputs:
                raise RuntimeError(
                    f"{self.executable_candidates[0]} completed without expected outputs"
                )
            metadata = write_metadata(
                context.work_dir / f"{self.name}_run_metadata.json",
                {
                    "skill": self.name,
                    "tool": self.executable_candidates[0],
                    "tool_source": tool_command.source,
                    "official_url": self.official_url,
                    "command": command,
                    "inputs": [str(path) for path in context.inputs],
                    "outputs": [str(path) for path in outputs],
                },
            )
            return SkillResult(
                "succeeded",
                [str(path) for path in outputs] + [str(metadata)],
                {"input_count": len(context.inputs), "output_count": len(outputs)},
                [],
            )
        except subprocess.TimeoutExpired:
            return SkillResult(
                "failed", [], {}, [], f"{self.executable_candidates[0]} timed out"
            )
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


def object_schema(properties: dict, required: list[str] | None = None) -> dict:
    schema = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema

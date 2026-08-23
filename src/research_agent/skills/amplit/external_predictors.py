from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from research_agent.skills.ancient_dna.common import run_command, write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import ToolCommand, resolve_tool


def _schema(properties: dict | None = None, required: list[str] | None = None) -> dict:
    schema = {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


class PeptideExternalCliSkill(ABC):
    resource_class = "heavy"
    timeout_seconds = 3600
    executable_candidates: tuple[str, ...]
    official_url: str
    installation_hint: str
    input_formats = {"csv", "fasta"}
    output_formats = {"csv", "json"}

    def find_tool_command(self) -> ToolCommand | None:
        return resolve_tool(self.executable_candidates)

    def find_executable(self) -> str | None:
        tool_command = self.find_tool_command()
        return tool_command.command[-1] if tool_command else None

    @abstractmethod
    def build_command(self, context: SkillContext, parameters: dict, executable: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def expected_outputs(self, context: SkillContext, parameters: dict) -> list[Path]:
        raise NotImplementedError

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = self.find_tool_command()
        if tool_command is None:
            tool = self.executable_candidates[0]
            return SkillResult(
                "dependency_missing",
                [],
                {
                    "dependency_report": {
                        "tool": tool,
                        "official_url": self.official_url,
                        "installation_instructions": [
                            self.installation_hint,
                            "Install the tool in a dedicated environment and restart the Agent.",
                            "The Agent will not install external software automatically.",
                        ],
                    }
                },
                [],
                f"Required tool is missing: {tool}. {self.installation_hint}",
            )
        try:
            for source in context.inputs:
                if not source.exists():
                    raise ValueError(f"Input does not exist: {source}")
            context.work_dir.mkdir(parents=True, exist_ok=True)
            command = self.build_command(
                context, parameters, tool_command.tool
            )
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
                    f"{self.executable_candidates[0]} exited with code {completed.returncode}: {completed.stderr.strip()}"
                )
            outputs = [path for path in self.expected_outputs(context, parameters) if path.exists()]
            if not outputs:
                raise RuntimeError(f"{self.executable_candidates[0]} completed without expected outputs")
            metadata = write_metadata(
                context.work_dir / f"{self.name}_run_metadata.json",
                {
                    "skill": self.name,
                    "tool": self.executable_candidates[0],
                    "tool_source": tool_command.source,
                    "official_url": self.official_url,
                    "command": command,
                    "outputs": [str(path) for path in outputs],
                },
            )
            return SkillResult("succeeded", [str(path) for path in outputs] + [str(metadata)], {"output_count": len(outputs)}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], f"{self.executable_candidates[0]} timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class AmplifyPredictionSkill(PeptideExternalCliSkill):
    name = "amplify_prediction"
    description = "Run a local AMPlify antimicrobial peptide prediction command on peptide FASTA or CSV input."
    executable_candidates = ("amplify", "AMPlify")
    official_url = "https://github.com/bcgsc/AMPlify"
    installation_hint = "Install AMPlify and expose its prediction command on PATH."
    parameter_schema = _schema()

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "--input", str(context.inputs[0]),
            "--output", str(context.work_dir / "amplify_predictions.csv"),
        ]

    def expected_outputs(self, context, parameters):
        return [context.work_dir / "amplify_predictions.csv"]


class AmpScannerPredictionSkill(PeptideExternalCliSkill):
    name = "amp_scanner_prediction"
    description = "Run a local AMP Scanner prediction command on peptide FASTA or CSV input."
    executable_candidates = ("amp-scanner", "ampscanner", "AMPScanner")
    official_url = "https://github.com/dwylab/AMP_Scanner"
    installation_hint = "Install AMP Scanner and expose its prediction command on PATH."
    parameter_schema = _schema()

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "--input", str(context.inputs[0]),
            "--output", str(context.work_dir / "amp_scanner_predictions.csv"),
        ]

    def expected_outputs(self, context, parameters):
        return [context.work_dir / "amp_scanner_predictions.csv"]


class ModlampDescriptorSkill(PeptideExternalCliSkill):
    name = "modlamp_descriptor"
    description = "Run a local modlAMP descriptor workflow for peptide feature extraction or AMP scoring."
    executable_candidates = ("modlamp", "modlamp-descriptors")
    official_url = "https://github.com/alexarnimueller/modlAMP"
    installation_hint = "Install modlAMP in Python and expose a local descriptor command on PATH."
    parameter_schema = _schema()

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "--input", str(context.inputs[0]),
            "--output", str(context.work_dir / "modlamp_descriptors.csv"),
        ]

    def expected_outputs(self, context, parameters):
        return [context.work_dir / "modlamp_descriptors.csv"]


def external_amp_predictor_skills():
    return [
        AmplifyPredictionSkill(),
        AmpScannerPredictionSkill(),
        ModlampDescriptorSkill(),
    ]

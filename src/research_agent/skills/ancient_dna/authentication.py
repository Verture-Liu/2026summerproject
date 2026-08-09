from __future__ import annotations

import subprocess
from pathlib import Path

from research_agent.skills.ancient_dna.common import run_command, write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import resolve_tool


MAPDAMAGE_URL = "https://github.com/ginolhac/mapDamage"


class AncientDnaAuthenticationSkill:
    name = "ancient_dna_authentication"
    description = "Estimate ancient-DNA terminal damage patterns from an aligned BAM using mapDamage."
    input_formats = {"bam"}
    output_formats = {"pdf", "txt", "json"}
    resource_class = "heavy"
    min_inputs = 1
    max_inputs = 1
    parameter_schema = {
        "type": "object",
        "required": ["reference"],
        "properties": {
            "reference": {"type": "string"},
            "downsample": {"type": "integer", "minimum": 1},
        },
        "additionalProperties": False,
    }

    def check_readiness(self) -> dict:
        missing = [
            name
            for name, candidates in (
                ("mapDamage", ("mapDamage", "mapDamage2")),
                ("samtools", ("samtools",)),
            )
            if resolve_tool(candidates) is None
        ]
        return {
            "ready": not missing,
            "tool": ", ".join(missing) if missing else "mapDamage + samtools",
            "missing": missing,
            "official_url": MAPDAMAGE_URL,
            "installation_instructions": [
                "Install mapDamage and Samtools in dedicated conda/mamba environments.",
                "Configure those environments in config/tool_envs.json when the commands are not on PATH.",
                "PaleoRigor will not install external software automatically.",
            ],
        }

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        executable = resolve_tool(("mapDamage", "mapDamage2"))
        samtools = resolve_tool(("samtools",))
        missing = []
        if executable is None:
            missing.append("mapDamage")
        if samtools is None:
            missing.append("samtools")
        if missing:
            instructions = [
                "Install mapDamage and Samtools in a dedicated conda/mamba environment.",
                "Confirm mapDamage (or mapDamage2) and samtools are available on PATH or in config/tool_envs.json conda environments.",
                "Example checks: conda run -n mapdamage_env mapDamage --version; conda run -n samtools_env samtools --version",
            ]
            return SkillResult(
                "dependency_missing",
                [],
                {
                    "dependency_report": {
                        "ready": False,
                        "missing": missing,
                        "official_url": MAPDAMAGE_URL,
                        "installation_instructions": instructions,
                    }
                },
                [],
                "Missing required tools: " + ", ".join(missing) + ". " + " ".join(instructions),
            )
        try:
            if len(context.inputs) != 1 or not context.inputs[0].is_file():
                raise ValueError("Ancient DNA authentication requires one existing BAM file")
            reference = Path(str(parameters["reference"])).expanduser()
            if not reference.is_file():
                raise ValueError(f"Reference FASTA does not exist: {reference}")
            context.work_dir.mkdir(parents=True, exist_ok=True)
            output_dir = context.work_dir / "mapdamage"
            command = [
                *executable.command,
                "-i", str(context.inputs[0]),
                "-r", str(reference),
                "-d", str(output_dir),
            ]
            if "downsample" in parameters:
                command += ["--downsample", str(parameters["downsample"])]
            completed = run_command(
                command,
                cwd=context.work_dir,
                stdout_path=context.work_dir / "mapdamage_stdout.log",
                stderr_path=context.work_dir / "mapdamage_stderr.log",
                timeout=24 * 3600,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"mapDamage exited with code {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                )
            outputs = sorted(path for path in output_dir.rglob("*") if path.is_file())
            if not outputs:
                raise RuntimeError("mapDamage completed without producing output files")
            metadata = write_metadata(
                context.work_dir / "mapdamage_run_metadata.json",
                {
                    "tool": "mapDamage",
                    "official_url": MAPDAMAGE_URL,
                    "tool_source": executable.source,
                    "samtools_source": samtools.source,
                    "input_bam": str(context.inputs[0]),
                    "reference": str(reference),
                    "downsample": parameters.get("downsample"),
                },
            )
            return SkillResult(
                "succeeded",
                [str(path) for path in outputs] + [str(metadata)],
                {"output_files": len(outputs)},
                [],
            )
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "mapDamage timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))

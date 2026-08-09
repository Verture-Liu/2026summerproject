from __future__ import annotations

import subprocess
from pathlib import Path

from research_agent.skills.ancient_dna.common import run_command, write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import resolve_tool


BOWTIE2_URL = "https://github.com/BenLangmead/bowtie2"
SAMTOOLS_URL = "https://github.com/samtools/samtools"


class HostDnaRemovalSkill:
    name = "host_dna_removal"
    description = "Cleaning stage: remove FASTQ reads aligning to a configured human reference with Bowtie2 before downstream microbiome or ancient-DNA analysis."
    input_formats = {"fastq"}
    output_formats = {"fastq", "txt", "json"}
    resource_class = "heavy"
    min_inputs = 1
    max_inputs = 2
    parameter_schema = {
        "type": "object",
        "required": ["reference"],
        "properties": {
            "reference": {"type": "string"},
            "threads": {"type": "integer", "minimum": 1, "maximum": 64},
        },
        "additionalProperties": False,
    }

    def check_readiness(self) -> dict:
        missing = [
            name
            for name, candidates in (
                ("bowtie2", ("bowtie2",)),
                ("samtools", ("samtools",)),
            )
            if resolve_tool(candidates) is None
        ]
        return {
            "ready": not missing,
            "tool": ", ".join(missing) if missing else "bowtie2 + samtools",
            "missing": missing,
            "official_urls": [BOWTIE2_URL, SAMTOOLS_URL],
            "installation_instructions": [
                "Install Bowtie2 and Samtools with conda/mamba, Homebrew, or your system package manager.",
                "Build a human reference index with bowtie2-build.",
                "Configure conda environments in config/tool_envs.json when the commands are not on PATH.",
                "PaleoRigor will not install external software automatically.",
            ],
        }

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        bowtie2 = resolve_tool(("bowtie2",))
        samtools = resolve_tool(("samtools",))
        missing = [
            name
            for name, tool_command in (("bowtie2", bowtie2), ("samtools", samtools))
            if tool_command is None
        ]
        if missing:
            instructions = [
                "Install Bowtie2 and Samtools with conda/mamba, Homebrew, or your system package manager.",
                "Build a human reference index with bowtie2-build.",
                "Confirm both commands are available on PATH or in config/tool_envs.json conda environments.",
                "Example checks: conda run -n bowtie2_env bowtie2 --version; conda run -n samtools_env samtools --version",
            ]
            return SkillResult(
                "dependency_missing",
                [],
                {
                    "dependency_report": {
                        "ready": False,
                        "missing": missing,
                        "official_urls": [BOWTIE2_URL, SAMTOOLS_URL],
                        "installation_instructions": instructions,
                    }
                },
                [],
                "Missing required tools: " + ", ".join(missing) + ". " + " ".join(instructions),
            )
        try:
            if len(context.inputs) not in {1, 2}:
                raise ValueError("Host removal accepts one single-end or two paired-end FASTQ files")
            for source in context.inputs:
                if not source.is_file():
                    raise ValueError(f"FASTQ input does not exist: {source}")
            reference = str(parameters["reference"]).strip()
            if not reference:
                raise ValueError("reference must be a Bowtie2 index prefix")
            threads = int(parameters.get("threads", 4))
            context.work_dir.mkdir(parents=True, exist_ok=True)
            metrics_path = context.work_dir / "bowtie2_metrics.txt"
            command = [
                *bowtie2.command,
                "--threads", str(threads),
                "--very-sensitive",
                "-x", reference,
                "--met-file", str(metrics_path),
            ]
            if len(context.inputs) == 1:
                output_paths = [context.work_dir / "host_removed.fastq.gz"]
                command += [
                    "-U", str(context.inputs[0]),
                    "--un-gz", str(output_paths[0]),
                ]
            else:
                pattern = context.work_dir / "host_removed_%.fastq.gz"
                output_paths = [
                    context.work_dir / "host_removed_1.fastq.gz",
                    context.work_dir / "host_removed_2.fastq.gz",
                ]
                command += [
                    "-1", str(context.inputs[0]),
                    "-2", str(context.inputs[1]),
                    "--un-conc-gz", str(pattern),
                ]
            command += ["-S", str(context.work_dir / "host_alignment.sam")]
            completed = run_command(
                command,
                cwd=context.work_dir,
                stdout_path=context.work_dir / "bowtie2_stdout.log",
                stderr_path=context.work_dir / "bowtie2_stderr.log",
                timeout=24 * 3600,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"Bowtie2 exited with code {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                )
            missing_outputs = [path for path in output_paths if not path.is_file()]
            if missing_outputs:
                raise RuntimeError(
                    "Bowtie2 did not create expected host-removed FASTQ files: "
                    + ", ".join(str(path) for path in missing_outputs)
                )
            metadata = write_metadata(
                context.work_dir / "host_removal_metadata.json",
                {
                    "tool": "Bowtie2",
                    "official_url": BOWTIE2_URL,
                    "tool_source": bowtie2.source,
                    "samtools_source": samtools.source,
                    "reference_index": reference,
                    "paired": len(context.inputs) == 2,
                    "threads": threads,
                },
            )
            outputs = output_paths + ([metrics_path] if metrics_path.exists() else [])
            return SkillResult(
                "succeeded",
                [str(path) for path in outputs] + [str(metadata)],
                {"input_files": len(context.inputs), "output_fastq_files": len(output_paths)},
                [],
            )
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "Host DNA removal timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))

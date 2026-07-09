from __future__ import annotations

import gzip
import subprocess
from pathlib import Path

from research_agent.skills.ancient_dna.common import run_command, write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import resolve_tool


FASTQC_URL = "https://www.bioinformatics.babraham.ac.uk/projects/fastqc/"
REVIEWED_SKILL_URL = "https://github.com/ubcd-ibfg/fastq-qc-skill"


def _open_fastq_text(path: Path):
    if path.name.lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _fastq_sequence_metrics(path: Path) -> dict:
    records = 0
    total_bases = 0
    gc_bases = 0
    n_bases = 0
    min_length = None
    max_length = None
    malformed_records = 0
    with _open_fastq_text(path) as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline().strip().upper()
            plus = handle.readline()
            quality = handle.readline().strip()
            if not sequence or not plus or not quality:
                malformed_records += 1
                break
            records += 1
            length = len(sequence)
            total_bases += length
            gc_bases += sequence.count("G") + sequence.count("C")
            n_bases += sequence.count("N")
            min_length = length if min_length is None else min(min_length, length)
            max_length = length if max_length is None else max(max_length, length)
            if not header.startswith("@") or not plus.startswith("+") or len(quality) != length:
                malformed_records += 1
    return {
        "path": str(path),
        "name": path.name,
        "records": records,
        "total_bases": total_bases,
        "min_length": min_length,
        "max_length": max_length,
        "mean_length": round(total_bases / records, 3) if records else None,
        "gc_percent": round(gc_bases / total_bases * 100, 3) if total_bases else None,
        "n_fraction": round(n_bases / total_bases, 6) if total_bases else None,
        "malformed_records": malformed_records,
    }


class FastqQcSkill:
    name = "fastq_qc"
    description = "Raw QC stage: run FastQC on one or more FASTQ files before cleaning, host removal, or downstream analysis."
    input_formats = {"fastq"}
    output_formats = {"html", "zip", "json"}
    resource_class = "heavy"
    parameter_schema = {
        "type": "object",
        "properties": {
            "threads": {"type": "integer", "minimum": 1, "maximum": 32},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = resolve_tool(("fastqc",))
        report = {
            "ready": tool_command is not None,
            "tool": "FastQC",
            "executable": " ".join(tool_command.command) if tool_command else "",
            "source": tool_command.source if tool_command else "",
            "official_url": FASTQC_URL,
            "reviewed_skill_source": REVIEWED_SKILL_URL,
            "installation_instructions": [
                "Install FastQC with conda/mamba, Homebrew, or your system package manager.",
                "Confirm installation by running: fastqc --version",
                "Restart the Agent after FastQC is available on PATH.",
            ],
        }
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"dependency_report": report},
                [],
                "FastQC is not installed. " + " ".join(report["installation_instructions"]),
            )
        try:
            for source in context.inputs:
                if not source.is_file():
                    raise ValueError(f"FASTQ input does not exist: {source}")
            context.work_dir.mkdir(parents=True, exist_ok=True)
            output_dir = context.work_dir / "fastqc"
            output_dir.mkdir(exist_ok=True)
            threads = int(parameters.get("threads", min(len(context.inputs), 4)))
            completed = run_command(
                [
                    *tool_command.command,
                    "--outdir", str(output_dir),
                    "--threads", str(threads),
                    *[str(path) for path in context.inputs],
                ],
                cwd=context.work_dir,
                stdout_path=context.work_dir / "fastqc_stdout.log",
                stderr_path=context.work_dir / "fastqc_stderr.log",
                timeout=3600,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"FastQC exited with code {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                )
            html_reports = sorted(output_dir.glob("*_fastqc.html"))
            zip_reports = sorted(output_dir.glob("*_fastqc.zip"))
            reports = html_reports + zip_reports
            if not reports:
                raise RuntimeError("FastQC completed without producing reports")
            metadata = write_metadata(
                context.work_dir / "fastqc_run_metadata.json",
                {
                    "tool": "FastQC",
                    "official_url": FASTQC_URL,
                    "reviewed_skill_source": REVIEWED_SKILL_URL,
                    "inputs": [str(path) for path in context.inputs],
                    "input_metrics": [
                        _fastq_sequence_metrics(path) for path in context.inputs
                    ],
                    "threads": threads,
                    "reports": [str(path) for path in reports],
                },
            )
            return SkillResult(
                "succeeded",
                [str(path) for path in html_reports]
                + [str(metadata)]
                + [str(path) for path in zip_reports],
                {"input_files": len(context.inputs), "report_files": len(reports)},
                [],
            )
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "FastQC timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))

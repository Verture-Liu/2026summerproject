from __future__ import annotations

import shutil
import subprocess
import gzip
from pathlib import Path

from research_agent.skills.ancient_dna.common import write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import resolve_tool, run_tool_command


SEQKIT_URL = "https://bioinf.shenwei.me/seqkit/"


def _json_schema(properties: dict | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": False,
    }


def _require_seqkit() -> str | None:
    tool_command = resolve_tool(("seqkit",))
    return " ".join(tool_command.command) if tool_command else None


def _require_seqkit_command():
    return resolve_tool(("seqkit",))


def _sequence_suffix(path: Path) -> str:
    name = path.name.lower()
    if any(token in name for token in (".fa", ".fasta", ".fna", ".faa")):
        return ".fasta"
    return ".fastq"


class SeqkitStatsSkill:
    name = "seqkit_stats"
    description = "Run seqkit stats on FASTA or FASTQ files to summarize sequence counts and lengths."
    input_formats = {"fasta", "fastq"}
    output_formats = {"tsv", "json"}
    resource_class = "medium"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = _require_seqkit_command()
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"official_url": SEQKIT_URL},
                [],
                "seqkit is not installed. Install seqkit, then confirm: seqkit version",
            )
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            output = context.work_dir / "seqkit_stats.tsv"
            args = ["stats", "-T", "-o", str(output), *[str(path) for path in context.inputs]]
            completed = run_tool_command(tool_command, args, cwd=context.work_dir, timeout=3600)
            (context.work_dir / "seqkit_stats_stdout.log").write_text(completed.stdout, encoding="utf-8")
            (context.work_dir / "seqkit_stats_stderr.log").write_text(completed.stderr, encoding="utf-8")
            if completed.returncode:
                raise RuntimeError(f"seqkit stats exited with code {completed.returncode}: {completed.stderr.strip()}")
            metadata = write_metadata(
                context.work_dir / "seqkit_stats_metadata.json",
                {"tool": "seqkit", "tool_source": tool_command.source, "official_url": SEQKIT_URL, "inputs": [str(path) for path in context.inputs]},
            )
            return SkillResult("succeeded", [str(output), str(metadata)], {"input_files": len(context.inputs)}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "seqkit stats timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class SeqkitLengthFilterSkill:
    name = "seqkit_length_filter"
    description = "Filter FASTA or FASTQ sequences by minimum and maximum sequence length with seqkit."
    input_formats = {"fasta", "fastq"}
    output_formats = {"fasta", "fastq", "json"}
    resource_class = "medium"
    parameter_schema = _json_schema(
        {
            "min_length": {"type": "integer", "minimum": 1},
            "max_length": {"type": "integer", "minimum": 1},
        }
    )

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = _require_seqkit_command()
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"official_url": SEQKIT_URL},
                [],
                "seqkit is not installed. Install seqkit, then confirm: seqkit version",
            )
        if "min_length" not in parameters and "max_length" not in parameters:
            return SkillResult("failed", [], {}, [], "Provide min_length and/or max_length")
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            if not context.inputs:
                raise ValueError("No sequence input provided")
            source = context.inputs[0]
            output = context.work_dir / f"length_filtered{_sequence_suffix(source)}"
            args = ["seq"]
            if "min_length" in parameters:
                args.extend(["-m", str(parameters["min_length"])])
            if "max_length" in parameters:
                args.extend(["-M", str(parameters["max_length"])])
            args.extend(["-o", str(output), str(source)])
            completed = run_tool_command(tool_command, args, cwd=context.work_dir, timeout=3600)
            (context.work_dir / "seqkit_length_filter_stdout.log").write_text(completed.stdout, encoding="utf-8")
            (context.work_dir / "seqkit_length_filter_stderr.log").write_text(completed.stderr, encoding="utf-8")
            if completed.returncode:
                raise RuntimeError(f"seqkit seq exited with code {completed.returncode}: {completed.stderr.strip()}")
            metadata = write_metadata(
                context.work_dir / "seqkit_length_filter_metadata.json",
                {
                    "tool": "seqkit",
                    "tool_source": tool_command.source,
                    "official_url": SEQKIT_URL,
                    "input": str(source),
                    "output": str(output),
                    "parameters": parameters,
                },
            )
            return SkillResult("succeeded", [str(output), str(metadata)], {"output_sequences": None}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "seqkit length filter timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class SeqkitDeduplicateSkill:
    name = "seqkit_deduplicate"
    description = "Remove duplicate FASTA or FASTQ sequences with seqkit rmdup."
    input_formats = {"fasta", "fastq"}
    output_formats = {"fasta", "fastq", "json"}
    resource_class = "medium"
    parameter_schema = _json_schema(
        {
            "by_sequence": {"type": "boolean"},
        }
    )

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = _require_seqkit_command()
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"official_url": SEQKIT_URL},
                [],
                "seqkit is not installed. Install seqkit, then confirm: seqkit version",
            )
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            if not context.inputs:
                raise ValueError("No sequence input provided")
            source = context.inputs[0]
            output = context.work_dir / f"deduplicated{_sequence_suffix(source)}"
            args = ["rmdup"]
            if parameters.get("by_sequence", True):
                args.append("-s")
            args.extend(["-o", str(output), str(source)])
            completed = run_tool_command(tool_command, args, cwd=context.work_dir, timeout=3600)
            (context.work_dir / "seqkit_deduplicate_stdout.log").write_text(completed.stdout, encoding="utf-8")
            (context.work_dir / "seqkit_deduplicate_stderr.log").write_text(completed.stderr, encoding="utf-8")
            if completed.returncode:
                raise RuntimeError(f"seqkit rmdup exited with code {completed.returncode}: {completed.stderr.strip()}")
            metadata = write_metadata(
                context.work_dir / "seqkit_deduplicate_metadata.json",
                {
                    "tool": "seqkit",
                    "tool_source": tool_command.source,
                    "official_url": SEQKIT_URL,
                    "input": str(source),
                    "output": str(output),
                    "by_sequence": parameters.get("by_sequence", True),
                },
            )
            return SkillResult("succeeded", [str(output), str(metadata)], {}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "seqkit deduplicate timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class SeqtkSampleSkill:
    name = "seqtk_sample"
    description = "Subsample FASTA or FASTQ files with seqtk for small test runs."
    input_formats = {"fasta", "fastq"}
    output_formats = {"fasta", "fastq", "json"}
    resource_class = "medium"
    parameter_schema = _json_schema(
        {
            "fraction": {"type": "number", "exclusiveMinimum": 0, "maximum": 1},
            "seed": {"type": "integer", "minimum": 1},
        }
    )

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = resolve_tool(("seqtk",))
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"official_url": "https://github.com/lh3/seqtk"},
                [],
                "seqtk is not installed. Install seqtk, then confirm: seqtk",
            )
        if "fraction" not in parameters:
            return SkillResult("failed", [], {}, [], "Provide fraction, for example 0.1")
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            if not context.inputs:
                raise ValueError("No sequence input provided")
            source = context.inputs[0]
            output = context.work_dir / f"sampled{_sequence_suffix(source)}"
            args = [
                "sample",
                "-s",
                str(parameters.get("seed", 11)),
                str(source),
                str(parameters["fraction"]),
            ]
            completed = run_tool_command(
                tool_command,
                args,
                cwd=context.work_dir,
                timeout=3600,
            )
            (context.work_dir / "seqtk_sample_stderr.log").write_text(completed.stderr, encoding="utf-8")
            if completed.returncode:
                raise RuntimeError(f"seqtk sample exited with code {completed.returncode}: {completed.stderr.strip()}")
            output.write_text(completed.stdout, encoding="utf-8")
            metadata = write_metadata(
                context.work_dir / "seqtk_sample_metadata.json",
                {
                    "tool": "seqtk",
                    "tool_source": tool_command.source,
                    "official_url": "https://github.com/lh3/seqtk",
                    "input": str(source),
                    "output": str(output),
                    "parameters": parameters,
                },
            )
            return SkillResult("succeeded", [str(output), str(metadata)], {}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "seqtk sample timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class GzipDecompressSkill:
    name = "gzip_decompress"
    description = "Decompress gzip files such as .fastq.gz or .fasta.gz before local workflow steps."
    input_formats = {"gz"}
    output_formats = {"fastq", "fasta", "txt", "json"}
    resource_class = "light"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            outputs = []
            for source in context.inputs:
                if source.suffix.lower() != ".gz":
                    raise ValueError(f"Input is not a .gz file: {source}")
                target = context.work_dir / source.name[:-3]
                with gzip.open(source, "rb") as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                outputs.append(target)
            metadata = write_metadata(
                context.work_dir / "gzip_decompress_metadata.json",
                {"inputs": [str(path) for path in context.inputs], "outputs": [str(path) for path in outputs]},
            )
            return SkillResult("succeeded", [str(path) for path in outputs] + [str(metadata)], {"files": len(outputs)}, [])
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class GzipCompressSkill:
    name = "gzip_compress"
    description = "Compress FASTA, FASTQ, TSV, CSV, or text files with gzip for storage or transfer."
    input_formats = {"fasta", "fastq", "csv", "tsv", "txt"}
    output_formats = {"gz", "json"}
    resource_class = "light"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            outputs = []
            for source in context.inputs:
                target = context.work_dir / f"{source.name}.gz"
                with source.open("rb") as src, gzip.open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                outputs.append(target)
            metadata = write_metadata(
                context.work_dir / "gzip_compress_metadata.json",
                {"inputs": [str(path) for path in context.inputs], "outputs": [str(path) for path in outputs]},
            )
            return SkillResult("succeeded", [str(path) for path in outputs] + [str(metadata)], {"files": len(outputs)}, [])
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


def sequence_utility_skills():
    return [
        SeqkitStatsSkill(),
        SeqkitLengthFilterSkill(),
        SeqkitDeduplicateSkill(),
        SeqtkSampleSkill(),
        GzipDecompressSkill(),
        GzipCompressSkill(),
    ]

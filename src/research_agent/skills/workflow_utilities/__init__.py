from __future__ import annotations

import csv
import gzip
import json
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from research_agent.skills.ancient_dna.common import write_metadata
from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.conda_tools import resolve_tool, run_tool_command


MULTIQC_URL = "https://multiqc.info/"
CANONICAL_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def _fatal_quality_warnings(warnings: list[str]) -> list[str]:
    return [
        warning
        for warning in warnings
        if "duplicate sequence(s)" not in warning
    ]


def _json_schema(properties: dict | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": False,
    }


def _file_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith((".fastq.gz", ".fq.gz", ".fastq", ".fq")):
        return "fastq"
    if name.endswith((".fasta.gz", ".fa.gz", ".fna.gz", ".faa.gz", ".fasta", ".fa", ".fna", ".faa")):
        return "fasta"
    if name.endswith(".csv"):
        return "csv"
    if name.endswith(".tsv"):
        return "tsv"
    if name.endswith(".bam"):
        return "bam"
    if name.endswith(".sam"):
        return "sam"
    if name.endswith(".html"):
        return "html"
    if name.endswith(".zip"):
        return "zip"
    try:
        first = path.read_text(encoding="utf-8", errors="ignore")[:1024]
    except OSError:
        return "unknown"
    if first.startswith("@") and "\n+\n" in first:
        return "fastq"
    if first.startswith(">"):
        return "fasta"
    if "," in first.splitlines()[0]:
        return "csv"
    if "\t" in first.splitlines()[0]:
        return "tsv"
    return "unknown"


class FileTypeDetectSkill:
    name = "file_type_detect"
    description = "Detect common research file types before planning a workflow."
    input_formats = {"any"}
    output_formats = {"json"}
    resource_class = "light"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        context.work_dir.mkdir(parents=True, exist_ok=True)
        files = [
            {
                "path": str(path),
                "name": path.name,
                "format": _file_format(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "exists": path.exists(),
            }
            for path in context.inputs
        ]
        output = write_metadata(context.work_dir / "file_type_report.json", {"files": files})
        return SkillResult(
            "succeeded",
            [str(output)],
            {"files": len(files), "formats": sorted({item["format"] for item in files})},
            [],
        )


PAIR_PATTERNS = [
    (re.compile(r"(.+?)(?:[_\.-])R?1(?:[_\.-].*)?$", re.IGNORECASE), "R1"),
    (re.compile(r"(.+?)(?:[_\.-])R?2(?:[_\.-].*)?$", re.IGNORECASE), "R2"),
]


def _sample_and_mate(path: Path) -> tuple[str, str | None]:
    stem = path.name
    for suffix in (".fastq.gz", ".fq.gz", ".fastq", ".fq"):
        if stem.lower().endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    for pattern, mate in PAIR_PATTERNS:
        match = pattern.fullmatch(stem)
        if match:
            return match.group(1), mate
    return stem, None


class FastqPairMatchSkill:
    name = "fastq_pair_match"
    description = "Match FASTQ files into paired-end or single-end sample rows."
    input_formats = {"fastq"}
    output_formats = {"csv", "json"}
    resource_class = "light"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        context.work_dir.mkdir(parents=True, exist_ok=True)
        groups: dict[str, dict[str, Path]] = {}
        for path in sorted(context.inputs, key=lambda item: item.name):
            sample, mate = _sample_and_mate(path)
            groups.setdefault(sample, {})
            groups[sample][mate or "single"] = path
        rows = []
        warnings = []
        for sample, files in sorted(groups.items()):
            if "R1" in files and "R2" in files:
                rows.append(
                    {
                        "sample_id": sample,
                        "layout": "paired",
                        "fastq_1": str(files["R1"]),
                        "fastq_2": str(files["R2"]),
                    }
                )
            elif "single" in files:
                rows.append(
                    {
                        "sample_id": sample,
                        "layout": "single",
                        "fastq_1": str(files["single"]),
                        "fastq_2": "",
                    }
                )
            else:
                warnings.append(f"Incomplete pair for sample {sample}")
        csv_path = context.work_dir / "fastq_sample_sheet.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["sample_id", "layout", "fastq_1", "fastq_2"])
            writer.writeheader()
            writer.writerows(rows)
        json_path = write_metadata(context.work_dir / "fastq_pair_report.json", {"samples": rows})
        return SkillResult(
            "succeeded",
            [str(csv_path), str(json_path)],
            {"samples": len(rows), "warnings": len(warnings)},
            warnings,
        )


class ToolEnvironmentCheckSkill:
    name = "tool_environment_check"
    description = "Check whether local command-line tools needed by a workflow are available."
    input_formats = {"none"}
    output_formats = {"json"}
    resource_class = "light"
    parameter_schema = _json_schema(
        {
            "tools": {
                "type": "array",
                "items": {"type": "string"},
            }
        }
    )

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tools = parameters.get("tools") or [
            "multiqc",
            "seqkit",
            "seqtk",
            "pigz",
            "gzip",
            "fastqc",
            "bowtie2",
            "samtools",
            "mapDamage",
        ]
        context.work_dir.mkdir(parents=True, exist_ok=True)
        checks = []
        for tool in tools:
            tool_command = resolve_tool((tool,))
            checks.append(
                {
                    "tool": tool,
                    "path": " ".join(tool_command.command) if tool_command else None,
                    "source": tool_command.source if tool_command else None,
                }
            )
        output = write_metadata(context.work_dir / "tool_environment_report.json", {"tools": checks})
        missing = [item["tool"] for item in checks if item["path"] is None]
        available = [item["tool"] for item in checks if item["path"] is not None]
        return SkillResult(
            "succeeded" if not missing else "dependency_missing",
            [str(output)],
            {"available_tools": available, "missing_tools": missing},
            [],
            None if not missing else "Missing local tools: " + ", ".join(missing),
        )


def _open_text_maybe_gzip(path: Path):
    if path.name.lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _fastq_metrics(path: Path) -> dict:
    records = 0
    total_bases = 0
    min_length = None
    max_length = None
    n_bases = 0
    malformed = 0
    with _open_text_maybe_gzip(path) as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline().strip()
            plus = handle.readline()
            quality = handle.readline().strip()
            if not quality:
                malformed += 1
                break
            records += 1
            length = len(sequence)
            total_bases += length
            n_bases += sequence.upper().count("N")
            min_length = length if min_length is None else min(min_length, length)
            max_length = length if max_length is None else max(max_length, length)
            if not header.startswith("@") or not plus.startswith("+") or len(quality) != length:
                malformed += 1
    return {
        "format": "fastq",
        "records": records,
        "total_bases": total_bases,
        "min_length": min_length,
        "max_length": max_length,
        "mean_length": round(total_bases / records, 3) if records else None,
        "n_fraction": round(n_bases / total_bases, 6) if total_bases else None,
        "malformed_records": malformed,
    }


def _fasta_metrics(path: Path) -> dict:
    records = 0
    lengths = []
    current = 0
    with _open_text_maybe_gzip(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith(">"):
                if records:
                    lengths.append(current)
                records += 1
                current = 0
            elif line:
                current += len(line)
    if records:
        lengths.append(current)
    return {
        "format": "fasta",
        "records": records,
        "min_length": min(lengths) if lengths else None,
        "max_length": max(lengths) if lengths else None,
        "mean_length": round(sum(lengths) / len(lengths), 3) if lengths else None,
    }


class DataQualityGateSkill:
    name = "data_quality_gate"
    description = "Post-cleaning QC gate: check cleaned CSV, FASTA, or FASTQ outputs before downstream application analysis."
    input_formats = {"csv", "tsv", "fasta", "fastq"}
    output_formats = {"json"}
    resource_class = "light"
    parameter_schema = _json_schema(
        {
            "sequence_column": {"type": "string"},
            "label_column": {"type": "string"},
            "min_rows": {"type": "integer", "minimum": 1},
            "min_records": {"type": "integer", "minimum": 1},
            "fail_on_error": {"type": "boolean"},
        }
    )

    def _csv_metrics(self, path: Path, parameters: dict) -> tuple[dict, list[str]]:
        sep = "\t" if path.suffix.lower() == ".tsv" else ","
        frame = pd.read_csv(path, sep=sep, keep_default_na=False)
        warnings = []
        metrics = {
            "format": "tsv" if sep == "\t" else "csv",
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "empty_cells": int((frame.astype(str).apply(lambda col: col.str.strip() == "")).sum().sum()),
        }
        min_rows = int(parameters.get("min_rows", 1))
        if len(frame) < min_rows:
            warnings.append(f"{path.name}: row count {len(frame)} is below minimum {min_rows}")
        sequence_column = parameters.get("sequence_column") or ("sequence" if "sequence" in frame.columns else None)
        if sequence_column:
            if sequence_column not in frame.columns:
                warnings.append(f"{path.name}: sequence column not found: {sequence_column}")
            else:
                sequences = frame[sequence_column].astype(str).str.strip().str.upper()
                lengths = sequences.str.len()
                duplicate_count = int(sequences.duplicated().sum())
                invalid_count = int(
                    sequences.map(lambda seq: bool(set(seq) - CANONICAL_AMINO_ACIDS)).sum()
                )
                metrics.update(
                    {
                        "sequence_column": sequence_column,
                        "duplicate_sequences": duplicate_count,
                        "invalid_sequences": invalid_count,
                        "min_sequence_length": int(lengths.min()) if not lengths.empty else None,
                        "max_sequence_length": int(lengths.max()) if not lengths.empty else None,
                        "mean_sequence_length": round(float(lengths.mean()), 3) if not lengths.empty else None,
                    }
                )
                if duplicate_count:
                    warnings.append(f"{path.name}: {duplicate_count} duplicate sequence(s)")
                if invalid_count:
                    warnings.append(f"{path.name}: {invalid_count} sequence(s) contain invalid amino acid letters")
        label_column = parameters.get("label_column") or ("label" if "label" in frame.columns else None)
        if label_column and label_column in frame.columns:
            metrics["label_counts"] = {
                str(key): int(value)
                for key, value in frame[label_column].value_counts(dropna=False).to_dict().items()
            }
        return metrics, warnings

    def _file_metrics(self, path: Path, parameters: dict) -> tuple[dict, list[str]]:
        fmt = _file_format(path)
        if fmt in {"csv", "tsv"}:
            return self._csv_metrics(path, parameters)
        if fmt == "fastq":
            metrics = _fastq_metrics(path)
            warnings = []
            min_records = int(parameters.get("min_records", 1))
            if metrics["records"] < min_records:
                warnings.append(f"{path.name}: record count {metrics['records']} is below minimum {min_records}")
            if metrics["malformed_records"]:
                warnings.append(f"{path.name}: {metrics['malformed_records']} malformed FASTQ record(s)")
            if metrics["records"] == 0:
                warnings.append(f"{path.name}: FASTQ file has no records")
            return metrics, warnings
        if fmt == "fasta":
            metrics = _fasta_metrics(path)
            warnings = []
            min_records = int(parameters.get("min_records", 1))
            if metrics["records"] < min_records:
                warnings.append(f"{path.name}: record count {metrics['records']} is below minimum {min_records}")
            return metrics, warnings
        return {"format": fmt}, [f"{path.name}: unsupported quality-gate format: {fmt}"]

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            reports = []
            warnings = []
            for path in context.inputs:
                if not path.exists():
                    warnings.append(f"{path.name}: file does not exist")
                    reports.append({"path": str(path), "exists": False})
                    continue
                metrics, file_warnings = self._file_metrics(path, parameters)
                reports.append(
                    {
                        "path": str(path),
                        "name": path.name,
                        "size_bytes": path.stat().st_size,
                        **metrics,
                    }
                )
                warnings.extend(file_warnings)
            fastq_reports = [item for item in reports if item.get("format") == "fastq"]
            if len(fastq_reports) == 2 and fastq_reports[0].get("records") != fastq_reports[1].get("records"):
                warnings.append(
                    "paired FASTQ read counts differ: "
                    f"{fastq_reports[0]['name']}={fastq_reports[0].get('records')}, "
                    f"{fastq_reports[1]['name']}={fastq_reports[1].get('records')}"
                )
            gate_passed = not warnings
            report_path = write_metadata(
                context.work_dir / "data_quality_gate_report.json",
                {"gate_passed": gate_passed, "files": reports, "warnings": warnings},
            )
            fatal_warnings = _fatal_quality_warnings(warnings)
            status = "failed" if parameters.get("fail_on_error") and fatal_warnings else "succeeded"
            return SkillResult(
                status,
                [str(report_path)],
                {"gate_passed": gate_passed, "files": len(reports), "warnings": len(warnings)},
                warnings,
                None if status == "succeeded" else "; ".join(fatal_warnings),
            )
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class SampleSheetValidateSkill:
    name = "sample_sheet_validate"
    description = "Validate a sequencing sample sheet before running local FASTQ workflows."
    input_formats = {"csv", "tsv"}
    output_formats = {"json"}
    resource_class = "light"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        context.work_dir.mkdir(parents=True, exist_ok=True)
        if not context.inputs:
            return SkillResult("failed", [], {}, [], "No sample sheet provided")
        source = context.inputs[0]
        sep = "\t" if source.suffix.lower() == ".tsv" else ","
        frame = pd.read_csv(source, sep=sep, keep_default_na=False)
        errors = []
        required = {"sample_id", "fastq_1"}
        missing_columns = sorted(required - set(frame.columns))
        if missing_columns:
            errors.append("Missing columns: " + ", ".join(missing_columns))
        if "sample_id" in frame.columns:
            duplicates = sorted(frame.loc[frame["sample_id"].duplicated(), "sample_id"].unique())
            if duplicates:
                errors.append("Duplicate sample_id values: " + ", ".join(map(str, duplicates)))
        for column in ("fastq_1", "fastq_2"):
            if column not in frame.columns:
                continue
            for value in frame[column]:
                if not str(value).strip():
                    continue
                if not Path(str(value)).expanduser().exists():
                    errors.append(f"Missing file in {column}: {value}")
        output = write_metadata(
            context.work_dir / "sample_sheet_validation.json",
            {"rows": len(frame), "columns": list(frame.columns), "errors": errors},
        )
        return SkillResult(
            "succeeded" if not errors else "failed",
            [str(output)],
            {"samples": len(frame), "errors": len(errors)},
            [],
            None if not errors else "; ".join(errors),
        )


class MultiqcSummarySkill:
    name = "multiqc_summary"
    description = "Reporting stage: summarize FastQC and other local bioinformatics tool outputs into one MultiQC HTML report."
    input_formats = {"directory", "txt", "zip", "html", "json"}
    output_formats = {"html", "json"}
    resource_class = "medium"
    parameter_schema = _json_schema()

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        tool_command = resolve_tool(("multiqc",))
        if tool_command is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"official_url": MULTIQC_URL},
                [],
                "MultiQC is not installed. Install it with conda/mamba or pip, then confirm: multiqc --version",
            )
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            output_dir = context.work_dir / "multiqc"
            output_dir.mkdir(exist_ok=True)
            args = [
                "--outdir",
                str(output_dir),
                "--filename",
                "multiqc_report.html",
                *[str(path) for path in context.inputs],
            ]
            completed = run_tool_command(
                tool_command,
                args,
                cwd=context.work_dir,
                timeout=3600,
            )
            (context.work_dir / "multiqc_stdout.log").write_text(completed.stdout, encoding="utf-8")
            (context.work_dir / "multiqc_stderr.log").write_text(completed.stderr, encoding="utf-8")
            if completed.returncode:
                raise RuntimeError(f"MultiQC exited with code {completed.returncode}: {completed.stderr.strip()}")
            report = output_dir / "multiqc_report.html"
            if not report.exists():
                raise RuntimeError("MultiQC completed without producing multiqc_report.html")
            metadata = write_metadata(
                context.work_dir / "multiqc_run_metadata.json",
                {
                    "tool": "MultiQC",
                    "official_url": MULTIQC_URL,
                    "tool_source": tool_command.source,
                    "inputs": [str(path) for path in context.inputs],
                    "report": str(report),
                },
            )
            return SkillResult("succeeded", [str(report), str(metadata)], {"reports": 1}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "MultiQC timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


def workflow_utility_skills():
    return [
        FileTypeDetectSkill(),
        FastqPairMatchSkill(),
        ToolEnvironmentCheckSkill(),
        DataQualityGateSkill(),
        SampleSheetValidateSkill(),
        MultiqcSummarySkill(),
    ]

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


FINAL_OUTPUT_SUFFIXES = {
    ".csv",
    ".tsv",
    ".xlsx",
    ".json",
    ".html",
    ".htm",
    ".zip",
    ".txt",
    ".log",
    ".png",
    ".pdf",
    ".fasta",
    ".fa",
    ".fastq",
    ".fq",
    ".gz",
    ".bz2",
    ".sam",
    ".bam",
    ".bai",
    ".bed",
    ".rma6",
    ".biom",
    ".faa",
    ".fna",
}
RECORDS_DIR = "ResearchAgent Records"
FINAL_OUTPUTS_DIR = "final_outputs"
STEP_OUTPUTS_DIR = "step_outputs"
USER_FACING_SKILLS = {
    "peptide_statistics",
    "peptide_chart",
    "peptide_csv_export",
    "fastq_qc",
    "multiqc_summary",
    "file_type_detect",
    "sequence_stats",
    "sequence_sample",
    "sequence_convert",
    "host_dna_removal",
    "ancient_dna_authentication",
    "metaphlan_profile",
    "kraken2_classify",
    "malt_align",
    "metaspades_assembly",
    "megahit_assembly",
    "metabat2_binning",
    "checkm2_quality",
}


@dataclass(frozen=True)
class ExportedFile:
    path: Path
    sha256: str


@dataclass(frozen=True)
class ExportSummary:
    final_files: list[ExportedFile]
    records_dir: Path
    result_dir: Path
    final_outputs_dir: Path
    step_outputs_dir: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _available_destination(destination: Path, source: Path, task_id: str) -> Path:
    candidate = destination / source.name
    if not candidate.exists():
        return candidate
    return destination / f"{source.stem}_{task_id[:8]}{source.suffix}"


def _available_directory(destination: Path, name: str, task_id: str) -> Path:
    candidate = destination / name
    if not candidate.exists():
        return candidate
    return destination / f"{name}_{task_id[:8]}"


def _result_directory(destination: Path, task_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _available_directory(
        destination,
        f"ResearchAgent_Result_{timestamp}_{task_id[:8]}",
        task_id,
    )


def _manifest_steps(task_dir: Path) -> list[dict]:
    manifest_path = task_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    steps = manifest.get("steps", [])
    return steps if isinstance(steps, list) else []


def _manifest_user_facing_output_paths(task_dir: Path) -> list[Path]:
    paths = []
    for step in _manifest_steps(task_dir):
        if step.get("skill") not in USER_FACING_SKILLS:
            continue
        for output in step.get("outputs", []):
            path = output.get("path")
            if path:
                paths.append(Path(path))
    return paths


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    unique = []
    for path in paths:
        resolved = Path(path)
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return unique


def _safe_step_folder_name(step: dict) -> str:
    step_id = str(step.get("id") or "step")
    skill = str(step.get("skill") or "unknown")
    safe_skill = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in skill)
    return f"{step_id}_{safe_skill}"


def _copy_supported_files(sources: list[Path], destination: Path, task_id: str) -> list[ExportedFile]:
    destination.mkdir(parents=True, exist_ok=True)
    exported: list[ExportedFile] = []
    for source in sources:
        if not source.exists() or not source.is_file():
            continue
        if source.suffix.lower() not in FINAL_OUTPUT_SUFFIXES:
            continue
        target = _available_destination(destination, source, task_id)
        shutil.copy2(source, target)
        exported.append(ExportedFile(target, _sha256(target)))
    return exported


def _copy_step_outputs(task_dir: Path, step_outputs_dir: Path, task_id: str) -> list[ExportedFile]:
    exported: list[ExportedFile] = []
    for step in _manifest_steps(task_dir):
        step_dir = step_outputs_dir / _safe_step_folder_name(step)
        paths = [
            Path(output["path"])
            for output in step.get("outputs", [])
            if output.get("path")
        ]
        exported.extend(_copy_supported_files(_unique_paths(paths), step_dir, task_id))
    return exported


def export_task_results(
    outputs: list[Path],
    task_dir: Path,
    destination: Path,
    task_id: str,
) -> ExportSummary:
    task_dir = Path(task_dir)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    result_dir = _result_directory(destination, task_id)
    final_outputs_dir = result_dir / FINAL_OUTPUTS_DIR
    step_outputs_dir = result_dir / STEP_OUTPUTS_DIR
    records_dir = result_dir / RECORDS_DIR
    result_dir.mkdir(parents=True, exist_ok=True)

    final_deliverables = _unique_paths(
        _manifest_user_facing_output_paths(task_dir) + list(map(Path, outputs))
    )
    exported = _copy_supported_files(final_deliverables, final_outputs_dir, task_id)
    step_exported = _copy_step_outputs(task_dir, step_outputs_dir, task_id)

    records_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("report.html", "manifest.json"):
        source = task_dir / filename
        if source.exists():
            shutil.copy2(source, records_dir / filename)
    logs = task_dir / "logs"
    if logs.exists():
        shutil.copytree(logs, records_dir / "logs", dirs_exist_ok=True)

    exported_manifest = records_dir / "manifest.json"
    if exported_manifest.exists():
        manifest = json.loads(exported_manifest.read_text(encoding="utf-8"))
        manifest["exported_final_files"] = [
            {"path": str(item.path), "sha256": item.sha256}
            for item in exported
        ]
        manifest["exported_step_files"] = [
            {"path": str(item.path), "sha256": item.sha256}
            for item in step_exported
        ]
        manifest["export_result_directory"] = str(result_dir)
        exported_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return ExportSummary(exported, records_dir, result_dir, final_outputs_dir, step_outputs_dir)

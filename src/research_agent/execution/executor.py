import hashlib
import html
import json
import platform
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from research_agent.agent.refs import normalize_step_ref
from research_agent.skills.base import SkillContext


@dataclass(frozen=True)
class ExecutionSummary:
    status: str
    outputs: list[str]
    steps: list[dict]


FORMAT_SUFFIXES = {
    "csv": {".csv"},
    "tsv": {".tsv"},
    "xlsx": {".xlsx", ".xls"},
    "json": {".json"},
    "html": {".html", ".htm"},
    "zip": {".zip"},
    "txt": {".txt", ".log"},
    "png": {".png"},
    "pdf": {".pdf"},
    "fasta": {".fasta", ".fa", ".faa", ".fna"},
    "fastq": {".fastq", ".fq", ".gz"},
    "sam": {".sam"},
    "bam": {".bam"},
    "bai": {".bai"},
    "bed": {".bed"},
    "rma6": {".rma6"},
    "biom": {".biom"},
    "directory": set(),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_matches_format(path: Path, output_format: str) -> bool:
    if output_format == "directory":
        return path.is_dir()
    suffixes = {suffix.lower() for suffix in path.suffixes}
    expected = FORMAT_SUFFIXES.get(output_format, {f".{output_format}"})
    return bool(suffixes & expected)


def _select_declared_output(result_outputs: list[str], output_format: str, index: int, used: set[int]) -> Path | None:
    for result_index, result_output in enumerate(result_outputs):
        if result_index in used:
            continue
        output_path = Path(result_output)
        if _path_matches_format(output_path, output_format):
            used.add(result_index)
            return output_path
    if index < len(result_outputs) and index not in used:
        used.add(index)
        return Path(result_outputs[index])
    return None


def _write_report(task_dir: Path, workflow, steps: list[dict], outputs: list[str]) -> None:
    rows = "".join(
        f"<tr><td>{html.escape(step['id'])}</td><td>{html.escape(step['skill'])}</td>"
        f"<td>{html.escape(step['status'])}</td></tr>"
        for step in steps
    )
    links = "".join(
        f"<li>{html.escape(str(Path(path).name))}</li>" for path in outputs
    )
    page = (
        "<!doctype html><html><head><meta charset='utf-8'><title>Research Agent Report</title></head>"
        f"<body><h1>{html.escape(workflow.task_summary)}</h1>"
        f"<table><tr><th>Step</th><th>Skill</th><th>Status</th></tr>{rows}</table>"
        f"<h2>Outputs</h2><ul>{links}</ul></body></html>"
    )
    (task_dir / "report.html").write_text(page, encoding="utf-8")


def execute_workflow(workflow, task_dir: Path, uploaded_files: dict[str, Path], registry, settings: dict) -> ExecutionSummary:
    task_dir = Path(task_dir)
    step_outputs: dict[str, Path] = {}
    audit_steps: list[dict] = []
    final_outputs: list[str] = []
    status = "succeeded"
    for step in workflow.steps:
        work_dir = task_dir / "steps" / step.id
        work_dir.mkdir(parents=True, exist_ok=True)
        resolved_inputs = []
        for input_ref in step.inputs:
            if input_ref.source == "uploaded":
                resolved_inputs.append(uploaded_files[input_ref.ref])
            else:
                resolved_inputs.append(step_outputs[normalize_step_ref(input_ref.ref)])
        started = datetime.now(UTC)
        try:
            result = registry.get(step.skill).run(SkillContext(work_dir, resolved_inputs), step.parameters)
            used_result_outputs: set[int] = set()
            for index, output in enumerate(step.outputs):
                output_path = _select_declared_output(
                    result.outputs,
                    output.format,
                    index,
                    used_result_outputs,
                )
                if output_path is not None:
                    step_outputs[f"{step.id}.{output.name}"] = output_path
                    step_outputs[output.name] = output_path
            step_outputs[step.id] = work_dir
            final_outputs = result.outputs
            step_status = result.status
            error = result.error
            if step_status != "succeeded":
                status = "failed"
        except Exception as exc:
            step_status = "failed"
            error = str(exc)
            result = None
            status = "failed"
        ended = datetime.now(UTC)
        record = {
            "id": step.id,
            "skill": step.skill,
            "status": step_status,
            "parameters": step.parameters,
            "metrics": result.metrics if result else {},
            "warnings": result.warnings if result else [],
            "error": error,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "inputs": [str(path) for path in resolved_inputs],
            "outputs": [
                {"path": path, "sha256": _sha256(Path(path))}
                for path in (result.outputs if result else [])
            ],
        }
        (work_dir / "step.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        audit_steps.append(record)
        if status == "failed":
            break
    manifest = {
        "workflow_schema_version": workflow.schema_version,
        "status": status,
        "workflow": workflow.model_dump(),
        "inputs": [
            {"ref": ref, "path": str(path), "sha256": _sha256(path)}
            for ref, path in uploaded_files.items()
        ],
        "steps": audit_steps,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "settings": {**settings, "api_key": "***" if settings.get("api_key") else ""},
    }
    (task_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(task_dir, workflow, audit_steps, final_outputs)
    return ExecutionSummary(status, final_outputs, audit_steps)

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
    "fastq": {".fastq", ".fq"},
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


def _select_declared_output(
    result_outputs: list[str],
    named_outputs: dict[str, str],
    output_name: str,
    output_format: str,
    used: set[int],
) -> Path | None:
    explicitly_named = named_outputs.get(output_name)
    if explicitly_named is not None:
        explicit_path = Path(explicitly_named)
        try:
            result_index = [Path(path) for path in result_outputs].index(explicit_path)
        except ValueError as exc:
            raise RuntimeError(
                f"named output {output_name} is not present in the skill result"
            ) from exc
        if result_index in used:
            raise RuntimeError(f"named output {output_name} was already consumed")
        if not _path_matches_format(explicit_path, output_format):
            raise RuntimeError(
                f"named output {output_name} does not match declared format {output_format}"
            )
        used.add(result_index)
        return explicit_path

    candidates: list[tuple[int, Path]] = []
    for result_index, result_output in enumerate(result_outputs):
        if result_index in used:
            continue
        output_path = Path(result_output)
        if _path_matches_format(output_path, output_format):
            candidates.append((result_index, output_path))
    if not candidates:
        return None
    if len(candidates) > 1:
        raise RuntimeError(
            f"ambiguous declared output {output_name} ({output_format}): "
            "the skill produced multiple matching files without an explicit named output"
        )
    result_index, output_path = candidates[0]
    used.add(result_index)
    return output_path


def _resolve_declared_outputs(
    result_outputs: list[str],
    named_outputs: dict[str, str],
    declared_outputs,
) -> list[Path | None]:
    result_paths = [Path(path) for path in result_outputs]
    resolved: list[Path | None] = [None] * len(declared_outputs)
    used: set[int] = set()

    for declared_index, output in enumerate(declared_outputs):
        explicitly_named = named_outputs.get(output.name)
        if explicitly_named is None:
            continue
        explicit_path = Path(explicitly_named)
        try:
            result_index = result_paths.index(explicit_path)
        except ValueError as exc:
            raise RuntimeError(
                f"named output {output.name} is not present in the skill result"
            ) from exc
        if result_index in used:
            raise RuntimeError(f"named output {output.name} was already consumed")
        if not _path_matches_format(explicit_path, output.format):
            raise RuntimeError(
                f"named output {output.name} does not match declared format {output.format}"
            )
        resolved[declared_index] = explicit_path
        used.add(result_index)

    formats = dict.fromkeys(output.format for output in declared_outputs)
    for output_format in formats:
        unresolved = [
            index
            for index, output in enumerate(declared_outputs)
            if output.format == output_format and resolved[index] is None
        ]
        if not unresolved:
            continue
        candidates = [
            (index, path)
            for index, path in enumerate(result_paths)
            if index not in used and _path_matches_format(path, output_format)
        ]
        if len(candidates) == len(unresolved):
            for declared_index, (result_index, path) in zip(unresolved, candidates):
                resolved[declared_index] = path
                used.add(result_index)
            continue
        if len(candidates) > 1:
            output_name = declared_outputs[unresolved[0]].name
            raise RuntimeError(
                f"ambiguous declared output {output_name} ({output_format}): "
                "the skill produced multiple matching files without an explicit named output"
            )
    return resolved


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
            resolved_declared_outputs = _resolve_declared_outputs(
                result.outputs,
                result.named_outputs,
                step.outputs,
            )
            for output, output_path in zip(step.outputs, resolved_declared_outputs):
                if output_path is None and result.status == "succeeded":
                    raise RuntimeError(
                        f"{step.skill} did not produce declared output "
                        f"{output.name} ({output.format})"
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

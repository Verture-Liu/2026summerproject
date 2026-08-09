import json
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from research_agent.agent.models import Workflow
from research_agent.agent.planner import Planner
from research_agent.agent.validator import validate_workflow
from research_agent.execution.executor import execute_workflow
from research_agent.execution.exporter import export_task_results
from research_agent.files.inspector import inspect_file
from research_agent.files.native_dialog import choose_directory
from research_agent.files.output_destination import (
    load_output_directory,
    save_output_directory,
)
from research_agent.files.task_store import TaskStore
from research_agent.skills.registry import build_default_registry


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApiConfig(StrictRequest):
    base_url: str
    api_key: str
    model: str


class PlanRequest(StrictRequest):
    instruction: str
    api: ApiConfig


class ExecuteRequest(StrictRequest):
    approved: bool
    workflow: Workflow


def _index_path(task_dir: Path) -> Path:
    return task_dir / "inputs.json"


def _load_index(task_dir: Path) -> dict:
    path = _index_path(task_dir)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _save_index(task_dir: Path, index: dict) -> None:
    _index_path(task_dir).write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def create_app(
    task_root: Path | str = "workspace/tasks",
    directory_chooser=None,
) -> FastAPI:
    app = FastAPI(title="Local Research Agent")
    store = TaskStore(Path(task_root))
    registry = build_default_registry()
    web_dir = Path(__file__).parent / "web"
    directory_selector = directory_chooser or choose_directory

    @app.post("/api/tasks", status_code=201)
    def create_task():
        return {"task_id": store.create_task()}

    @app.get("/api/skills")
    def list_skills():
        return {
            "packages": registry.packages(),
            "skills": [
                {
                    "name": item.name,
                    "description": item.description,
                    "input_formats": item.input_formats,
                    "output_formats": item.output_formats,
                    "min_inputs": item.min_inputs,
                    "max_inputs": item.max_inputs,
                    "package_id": item.package_id,
                    "package_version": item.package_version,
                }
                for item in registry.catalog()
            ],
            "diagnostics": registry.diagnostics(),
        }

    @app.post("/api/tasks/{task_id}/files", status_code=201)
    async def upload_files(task_id: str, files: list[UploadFile] = File(...)):
        task_dir = store.task_dir(task_id)
        index = _load_index(task_dir)
        response = []
        for upload in files:
            stored = store.add_input(task_id, upload.filename or "upload.bin", upload.file)
            summary = inspect_file(stored.path)
            ref = stored.ref
            suffix = 2
            while ref in index:
                ref = f"{stored.ref}_{suffix}"
                suffix += 1
            index[ref] = {
                "path": str(stored.path),
                "sha256": stored.sha256,
                "summary": summary.to_dict(),
            }
            response.append({"ref": ref, **index[ref]})
        _save_index(task_dir, index)
        return {"files": response}

    @app.post("/api/tasks/{task_id}/plan")
    async def plan_task(task_id: str, request: PlanRequest):
        task_dir = store.task_dir(task_id)
        index = _load_index(task_dir)
        summaries = [{"ref": ref, **item["summary"]} for ref, item in index.items()]
        async with httpx.AsyncClient() as client:
            planner = Planner(
                client,
                request.api.base_url,
                request.api.api_key,
                request.api.model,
            )
            try:
                workflow = await planner.plan(request.instruction, summaries, registry.catalog())
            except Exception as exc:
                raise HTTPException(502, detail={"error": "planning_failed", "message": str(exc)}) from exc
        uploaded_formats = {ref: item["summary"]["format"] for ref, item in index.items()}
        uploaded_paths = {ref: Path(item["path"]) for ref, item in index.items()}
        report = validate_workflow(
            workflow,
            registry,
            uploaded_formats,
            uploaded_paths=uploaded_paths,
            check_dependencies=True,
        )
        (task_dir / "workflow.draft.json").write_text(workflow.model_dump_json(indent=2), encoding="utf-8")
        return {
            "workflow": workflow.model_dump(),
            "validation": {
                "valid": report.valid,
                "errors": report.errors,
                "warnings": report.warnings,
                "issues": [issue.to_dict() for issue in report.issues],
            },
        }

    @app.post("/api/tasks/{task_id}/select-output-directory")
    def select_output_directory(task_id: str):
        task_dir = store.task_dir(task_id)
        try:
            selected = directory_selector()
        except Exception as exc:
            raise HTTPException(
                500,
                detail={
                    "error": "output_directory_dialog_failed",
                    "message": str(exc),
                },
            ) from exc
        if not selected:
            raise HTTPException(400, detail={"error": "output_directory_not_selected"})
        try:
            save_output_directory(task_dir, Path(selected))
        except ValueError as exc:
            raise HTTPException(400, detail={"error": "invalid_output_directory"}) from exc
        return {"path": str(load_output_directory(task_dir))}

    @app.post("/api/tasks/{task_id}/execute")
    def execute_task(task_id: str, request: ExecuteRequest):
        if not request.approved:
            raise HTTPException(400, detail={"error": "approval_required"})
        task_dir = store.task_dir(task_id)
        output_directory = load_output_directory(task_dir)
        if output_directory is None:
            raise HTTPException(400, detail={"error": "output_directory_required"})
        index = _load_index(task_dir)
        uploaded_formats = {ref: item["summary"]["format"] for ref, item in index.items()}
        uploaded_paths = {ref: Path(item["path"]) for ref, item in index.items()}
        report = validate_workflow(
            request.workflow,
            registry,
            uploaded_formats,
            uploaded_paths=uploaded_paths,
            check_dependencies=True,
        )
        if not report.valid:
            raise HTTPException(
                400,
                detail={
                    "error": "workflow_invalid",
                    "details": report.errors,
                    "issues": [issue.to_dict() for issue in report.issues],
                },
            )
        (task_dir / "workflow.json").write_text(request.workflow.model_dump_json(indent=2), encoding="utf-8")
        uploaded_files = uploaded_paths
        summary = execute_workflow(request.workflow, task_dir, uploaded_files, registry, {"api_key": ""})
        export = export_task_results(
            outputs=[Path(path) for path in summary.outputs],
            task_dir=task_dir,
            destination=output_directory,
            task_id=task_id,
        )
        return {
            "status": summary.status,
            "outputs": summary.outputs,
            "exported_files": [
                {"path": str(item.path), "sha256": item.sha256}
                for item in export.final_files
            ],
            "result_directory": str(export.result_dir),
            "final_outputs_directory": str(export.final_outputs_dir),
            "step_outputs_directory": str(export.step_outputs_dir),
            "records_directory": str(export.records_dir),
            "steps": summary.steps,
        }

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str):
        task_dir = store.task_dir(task_id)
        return {
            "task_id": task_id,
            "files": _load_index(task_dir),
            "has_report": (task_dir / "report.html").exists(),
        }

    @app.get("/api/tasks/{task_id}/report")
    def get_report(task_id: str):
        report = store.task_dir(task_id) / "report.html"
        if not report.exists():
            raise HTTPException(404, detail="Report not found")
        return FileResponse(report)

    app.mount("/assets", StaticFiles(directory=web_dir), name="assets")

    @app.get("/")
    def index():
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from starlette.concurrency import run_in_threadpool

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
from research_agent.runtime.configuration import RuntimeConfiguration
from research_agent.runtime.paths import AppPaths, resource_root
from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secret_guard import (
    SecretContaminationError,
    assert_no_secret_contamination,
    write_guarded_json,
)
from research_agent.runtime.secrets import MacOSKeychainSecretStore
from research_agent.runtime.session import install_api_token_guard
from research_agent.skills.registry import build_default_registry


APPLICATION_VERSION = "0.2.0"
GITHUB_URL = "https://github.com/Verture-Liu/2026summerproject"


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuntimeConfigRequest(StrictRequest):
    base_url: str
    model: str
    api_key: str | None


class PlanRequest(StrictRequest):
    instruction: str


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


def _default_runtime_configuration() -> RuntimeConfiguration:
    preferences = JsonPreferences(AppPaths.for_runtime().preferences_file)
    return RuntimeConfiguration(preferences, MacOSKeychainSecretStore())


def _redacted_config(configuration: RuntimeConfiguration) -> dict[str, object]:
    config = configuration.get()
    return {
        "base_url": config.base_url,
        "model": config.model,
        "api_key_present": bool(config.api_key),
    }


def create_app(
    task_root: Path | str | None = None,
    directory_chooser=None,
    runtime_configuration: RuntimeConfiguration | None = None,
    session_token: str | None = None,
    planner_client_factory: Callable[[], httpx.AsyncClient] | None = None,
) -> FastAPI:
    app = FastAPI(title="Local Research Agent", version=APPLICATION_VERSION)
    store = TaskStore(Path(task_root or "workspace/tasks"))
    registry = build_default_registry()
    web_dir = Path(__file__).parent / "web"
    directory_selector = directory_chooser or choose_directory
    configuration = runtime_configuration or _default_runtime_configuration()
    configuration_mutation_lock = asyncio.Lock()
    client_factory = planner_client_factory or httpx.AsyncClient
    install_api_token_guard(app, session_token)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _exc):
        return JSONResponse(status_code=422, content={"detail": {"error": "invalid_request"}})

    async def configuration_snapshot():
        async with configuration_mutation_lock:
            return await run_in_threadpool(configuration.get)

    @app.get("/api/config")
    async def get_configuration():
        try:
            return RuntimeConfiguration._redacted(await configuration_snapshot())
        except Exception as exc:
            raise HTTPException(503, detail={"error": "configuration_unavailable"}) from exc

    @app.put("/api/config")
    async def update_configuration(request: RuntimeConfigRequest):
        try:
            async with configuration_mutation_lock:
                return await run_in_threadpool(
                    configuration.update,
                    request.base_url,
                    request.model,
                    request.api_key,
                )
        except ValueError as exc:
            raise HTTPException(422, detail={"error": "invalid_configuration"}) from exc
        except Exception as exc:
            raise HTTPException(503, detail={"error": "configuration_unavailable"}) from exc

    @app.delete("/api/config/key")
    async def delete_configuration_key():
        try:
            async with configuration_mutation_lock:
                await run_in_threadpool(configuration.delete_api_key)
                return await run_in_threadpool(_redacted_config, configuration)
        except Exception as exc:
            raise HTTPException(503, detail={"error": "configuration_unavailable"}) from exc

    @app.post("/api/config/test")
    async def test_configuration():
        config = await configuration_snapshot()
        if not config.api_key:
            raise HTTPException(401, detail={"error": "invalid_api_credentials"})
        try:
            async with client_factory() as client:
                planner = Planner(client, config.base_url, config.api_key, config.model)
                response_content = await planner._complete(
                    [
                        {
                            "role": "user",
                            "content": "Return a JSON object with a status field.",
                        }
                    ]
                )
            if not isinstance(json.loads(response_content), dict):
                raise ValueError("Expected a JSON object")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise HTTPException(401, detail={"error": "invalid_api_credentials"}) from exc
            raise HTTPException(503, detail={"error": "api_unreachable"}) from exc
        except httpx.RequestError as exc:
            raise HTTPException(503, detail={"error": "api_unreachable"}) from exc
        except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(502, detail={"error": "invalid_api_response"}) from exc
        return {"status": "ok", "model": config.model}

    @app.get("/api/about")
    def about():
        manifest_path = resource_root() / "resources" / "tool_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "version": APPLICATION_VERSION,
            "github_url": GITHUB_URL,
            "tools": [
                {"id": tool["id"], "version": tool["version"]}
                for tool in manifest["tools"]
            ],
        }

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.2.0"}

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
        try:
            config = await configuration_snapshot()
        except Exception as exc:
            raise HTTPException(503, detail={"error": "configuration_unavailable"}) from exc
        try:
            async with client_factory() as client:
                planner = Planner(client, config.base_url, config.api_key, config.model)
                workflow = await planner.plan(request.instruction, summaries, registry.catalog())
            workflow_payload = workflow.model_dump(mode="json")
            assert_no_secret_contamination(workflow_payload, config.api_key)
        except Exception as exc:
            raise HTTPException(502, detail={"error": "planning_failed"}) from exc
        uploaded_formats = {ref: item["summary"]["format"] for ref, item in index.items()}
        uploaded_paths = {ref: Path(item["path"]) for ref, item in index.items()}
        report = validate_workflow(
            workflow,
            registry,
            uploaded_formats,
            uploaded_paths=uploaded_paths,
            check_dependencies=True,
        )
        response_payload = {
            "workflow": workflow_payload,
            "validation": {
                "valid": report.valid,
                "errors": report.errors,
                "warnings": report.warnings,
                "issues": [issue.to_dict() for issue in report.issues],
            },
        }
        try:
            assert_no_secret_contamination(response_payload, config.api_key)
            write_guarded_json(
                task_dir / "workflow.draft.json",
                workflow_payload,
                config.api_key,
            )
        except SecretContaminationError as exc:
            raise HTTPException(502, detail={"error": "planning_failed"}) from exc
        return response_payload

    @app.post("/api/tasks/{task_id}/select-output-directory")
    def select_output_directory(task_id: str):
        task_dir = store.task_dir(task_id)
        try:
            selected = directory_selector()
        except Exception as exc:
            raise HTTPException(
                500,
                detail={"error": "output_directory_dialog_failed"},
            ) from exc
        if not selected:
            raise HTTPException(400, detail={"error": "output_directory_not_selected"})
        try:
            save_output_directory(task_dir, Path(selected))
        except ValueError as exc:
            raise HTTPException(400, detail={"error": "invalid_output_directory"}) from exc
        return {"path": str(load_output_directory(task_dir))}

    @app.post("/api/tasks/{task_id}/execute")
    async def execute_task(task_id: str, request: ExecuteRequest):
        if not request.approved:
            raise HTTPException(400, detail={"error": "approval_required"})
        task_dir = store.task_dir(task_id)
        try:
            config = await configuration_snapshot()
        except Exception as exc:
            raise HTTPException(503, detail={"error": "configuration_unavailable"}) from exc
        workflow_payload = request.workflow.model_dump(mode="json")
        try:
            assert_no_secret_contamination(workflow_payload, config.api_key)
        except SecretContaminationError as exc:
            raise HTTPException(400, detail={"error": "workflow_rejected"}) from exc
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
        write_guarded_json(
            task_dir / "workflow.json",
            workflow_payload,
            config.api_key,
        )
        uploaded_files = uploaded_paths
        summary = await run_in_threadpool(
            execute_workflow,
            request.workflow,
            task_dir,
            uploaded_files,
            registry,
            {"api_key": ""},
        )
        export = await run_in_threadpool(
            export_task_results,
            [Path(path) for path in summary.outputs],
            task_dir,
            output_directory,
            task_id,
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

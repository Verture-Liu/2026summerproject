import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from research_agent.main import PlanRequest, create_app


def test_plan_request_forbids_legacy_request_supplied_api_configuration():
    with pytest.raises(ValidationError):
        PlanRequest.model_validate(
            {
                "instruction": "filter peptides",
                "api": {
                    "base_url": "https://provider.example/v1",
                    "model": "provider-model",
                    "api_key": "must-not-be-accepted",
                },
            }
        )


def test_create_task(tmp_path):
    client = TestClient(create_app(task_root=tmp_path))
    response = client.post("/api/tasks")
    assert response.status_code == 201
    assert response.json()["task_id"]


def test_list_skills_reports_loaded_packages(tmp_path):
    client = TestClient(create_app(task_root=tmp_path))
    response = client.get("/api/skills")
    assert response.status_code == 200
    data = response.json()
    assert {"peptide-table", "amplit", "legacy-core"}.issubset(
        {item["package_id"] for item in data["packages"]}
    )
    assert "amp_prediction" in {item["name"] for item in data["skills"]}
    assert isinstance(data["diagnostics"], list)


def test_execute_requires_approval(tmp_path):
    client = TestClient(create_app(task_root=tmp_path))
    task_id = client.post("/api/tasks").json()["task_id"]
    workflow = {
        "schema_version": "1.0",
        "task_summary": "filter",
        "steps": [
            {
                "id": "step_01",
                "skill": "peptide_filter",
                "inputs": [{"source": "uploaded", "ref": "peptides"}],
                "parameters": {"min_length": 13, "max_length": 26},
                "outputs": [{"name": "filtered", "format": "fasta"}],
                "reason": "filter",
            }
        ],
    }
    response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"approved": False, "workflow": workflow},
    )
    assert response.status_code == 400


def test_select_output_directory_saves_backend_chosen_path(tmp_path):
    destination = tmp_path / "chosen"
    destination.mkdir()
    client = TestClient(
        create_app(
            task_root=tmp_path / "tasks",
            directory_chooser=lambda: str(destination),
        )
    )
    task_id = client.post("/api/tasks").json()["task_id"]
    response = client.post(f"/api/tasks/{task_id}/select-output-directory")
    assert response.status_code == 200
    assert response.json()["path"] == str(destination.resolve())


def test_select_output_directory_reports_chooser_failure(tmp_path):
    def broken_chooser():
        raise RuntimeError("native dialog failed")

    client = TestClient(
        create_app(
            task_root=tmp_path / "tasks",
            directory_chooser=broken_chooser,
        )
    )
    task_id = client.post("/api/tasks").json()["task_id"]
    response = client.post(f"/api/tasks/{task_id}/select-output-directory")
    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "output_directory_dialog_failed"


def test_select_output_directory_does_not_echo_chooser_exception_details(tmp_path):
    provider_secret = "provider-secret-that-must-not-be-returned"

    def broken_chooser():
        raise RuntimeError(provider_secret)

    client = TestClient(
        create_app(
            task_root=tmp_path / "tasks",
            directory_chooser=broken_chooser,
        )
    )
    task_id = client.post("/api/tasks").json()["task_id"]

    response = client.post(f"/api/tasks/{task_id}/select-output-directory")

    assert response.status_code == 500
    assert response.json() == {"detail": {"error": "output_directory_dialog_failed"}}
    assert provider_secret not in response.text


def test_execute_requires_output_directory(tmp_path):
    client = TestClient(create_app(task_root=tmp_path))
    task_id = client.post("/api/tasks").json()["task_id"]
    workflow = {
        "schema_version": "1.0",
        "task_summary": "filter",
        "steps": [
            {
                "id": "step_01",
                "skill": "peptide_filter",
                "inputs": [{"source": "uploaded", "ref": "peptides"}],
                "parameters": {"min_length": 13, "max_length": 26},
                "outputs": [{"name": "filtered", "format": "fasta"}],
                "reason": "filter",
            }
        ],
    }
    response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"approved": True, "workflow": workflow},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "output_directory_required"


def test_execute_rejects_incompatible_input_with_structured_issue(tmp_path):
    destination = tmp_path / "results"
    destination.mkdir()
    client = TestClient(
        create_app(
            task_root=tmp_path / "tasks",
            directory_chooser=lambda: str(destination),
        )
    )
    task_id = client.post("/api/tasks").json()["task_id"]
    upload = client.post(
        f"/api/tasks/{task_id}/files",
        files={"files": ("Validation.csv", b"label,sequence\n1,ACDE\n", "text/csv")},
    )
    assert upload.status_code == 201
    ref = upload.json()["files"][0]["ref"]
    selected = client.post(f"/api/tasks/{task_id}/select-output-directory")
    assert selected.status_code == 200
    workflow = {
        "schema_version": "1.0",
        "task_summary": "run FastQC",
        "steps": [
            {
                "id": "step_01",
                "skill": "fastq_qc",
                "inputs": [{"source": "uploaded", "ref": ref}],
                "parameters": {},
                "outputs": [{"name": "qc_html", "format": "html"}],
                "reason": "quality control",
            }
        ],
    }

    response = client.post(
        f"/api/tasks/{task_id}/execute",
        json={"approved": True, "workflow": workflow},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "workflow_invalid"
    assert detail["issues"][0]["code"] == "input_format_incompatible"
    assert detail["issues"][0]["observed"] == "csv"
    assert detail["issues"][0]["expected"] == ["fastq"]

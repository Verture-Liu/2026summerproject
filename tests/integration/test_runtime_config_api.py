import json
from collections.abc import Mapping

import httpx
import pytest
from fastapi.testclient import TestClient

from research_agent.main import create_app
from research_agent.runtime.configuration import RuntimeConfiguration
from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secrets import MemorySecretStore


TEST_API_KEY = "task-6-test-api-key"


def assert_secret_absent(value):
    if isinstance(value, Mapping):
        for nested_value in value.values():
            assert_secret_absent(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            assert_secret_absent(nested_value)
    elif isinstance(value, str):
        assert TEST_API_KEY not in value


def make_client(tmp_path, handler):
    configuration = RuntimeConfiguration(
        JsonPreferences(tmp_path / "preferences.json"),
        MemorySecretStore(),
    )
    transport = httpx.MockTransport(handler)
    app = create_app(
        task_root=tmp_path / "tasks",
        runtime_configuration=configuration,
        planner_client_factory=lambda: httpx.AsyncClient(transport=transport),
    )
    return TestClient(app), configuration


def test_configuration_endpoints_redact_and_delete_the_stored_api_key(tmp_path):
    client, configuration = make_client(tmp_path, lambda request: httpx.Response(500))

    initial = client.get("/api/config")
    assert initial.status_code == 200
    assert initial.json() == {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "api_key_present": False,
    }

    updated = client.put(
        "/api/config",
        json={
            "base_url": "https://provider.example/v1",
            "model": "provider-model",
            "api_key": TEST_API_KEY,
        },
    )
    assert updated.status_code == 200
    assert updated.json() == {
        "base_url": "https://provider.example/v1",
        "model": "provider-model",
        "api_key_present": True,
    }
    assert configuration.get().api_key == TEST_API_KEY

    deleted = client.delete("/api/config/key")
    assert deleted.status_code == 200
    assert deleted.json() == {
        "base_url": "https://provider.example/v1",
        "model": "provider-model",
        "api_key_present": False,
    }
    assert configuration.get().api_key == ""

    for response in [initial, updated, deleted]:
        assert_secret_absent(response.json())
        assert_secret_absent(response.text)


def test_connection_test_uses_stored_configuration_and_returns_only_safe_fields(tmp_path):
    received = []

    def handler(request):
        received.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"status":"ok"}'}}]},
        )

    client, _ = make_client(tmp_path, handler)
    configured = client.put(
        "/api/config",
        json={
            "base_url": "https://provider.example/v1",
            "model": "provider-model",
            "api_key": TEST_API_KEY,
        },
    )
    assert configured.status_code == 200

    response = client.post("/api/config/test")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": "provider-model"}
    assert len(received) == 1
    request = received[0]
    assert str(request.url) == "https://provider.example/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {TEST_API_KEY}"
    request_body = json.loads(request.content)
    assert request_body["model"] == "provider-model"
    assert request_body["response_format"] == {"type": "json_object"}
    assert_secret_absent(response.json())
    assert_secret_absent(response.text)


def test_connection_test_maps_empty_provider_choices_to_invalid_api_response(tmp_path):
    client, _ = make_client(
        tmp_path,
        lambda request: httpx.Response(200, json={"choices": []}),
    )
    configured = client.put(
        "/api/config",
        json={
            "base_url": "https://provider.example/v1",
            "model": "provider-model",
            "api_key": TEST_API_KEY,
        },
    )
    assert configured.status_code == 200

    response = client.post("/api/config/test")

    assert response.status_code == 502
    assert response.json() == {"detail": {"error": "invalid_api_response"}}
    assert_secret_absent(response.json())
    assert_secret_absent(response.text)


@pytest.mark.parametrize(
    ("handler", "status_code", "error"),
    [
        (
            lambda request: httpx.Response(401, text=f"provider rejected {TEST_API_KEY}"),
            401,
            "invalid_api_credentials",
        ),
        (
            lambda request: httpx.Response(403, text=f"provider rejected {TEST_API_KEY}"),
            401,
            "invalid_api_credentials",
        ),
        (
            lambda request: (_ for _ in ()).throw(httpx.ConnectError(f"cannot reach {TEST_API_KEY}")),
            503,
            "api_unreachable",
        ),
        (
            lambda request: httpx.Response(200, json={"provider_error": TEST_API_KEY}),
            502,
            "invalid_api_response",
        ),
    ],
)
def test_connection_test_maps_provider_failures_without_disclosing_secrets(
    tmp_path, handler, status_code, error
):
    client, _ = make_client(tmp_path, handler)
    configured = client.put(
        "/api/config",
        json={
            "base_url": "https://provider.example/v1",
            "model": "provider-model",
            "api_key": TEST_API_KEY,
        },
    )
    assert configured.status_code == 200

    response = client.post("/api/config/test")

    assert response.status_code == status_code
    assert response.json() == {"detail": {"error": error}}
    assert_secret_absent(response.json())
    assert_secret_absent(response.text)


def test_planning_uses_stored_credentials_and_rejects_request_supplied_api_fields(tmp_path):
    received = []
    workflow_json = {
        "schema_version": "1.0",
        "task_summary": "filter peptides",
        "steps": [
            {
                "id": "step_01",
                "skill": "peptide_filter",
                "inputs": [{"source": "uploaded", "ref": "peptides"}],
                "parameters": {"min_length": 13, "max_length": 26},
                "outputs": [{"name": "filtered", "format": "fasta"}],
                "reason": "filter peptide lengths",
            }
        ],
    }

    def handler(request):
        received.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(workflow_json)}}]},
        )

    client, _ = make_client(tmp_path, handler)
    configured = client.put(
        "/api/config",
        json={
            "base_url": "https://provider.example/v1",
            "model": "provider-model",
            "api_key": TEST_API_KEY,
        },
    )
    assert configured.status_code == 200
    task_id = client.post("/api/tasks").json()["task_id"]

    planned = client.post(
        f"/api/tasks/{task_id}/plan",
        json={"instruction": "filter the uploaded peptide sequences"},
    )

    assert planned.status_code == 200
    assert planned.json()["workflow"]["task_summary"] == "filter peptides"
    assert len(received) == 1
    request = received[0]
    assert str(request.url) == "https://provider.example/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {TEST_API_KEY}"
    assert json.loads(request.content)["model"] == "provider-model"
    assert TEST_API_KEY not in request.content.decode()

    rejected = client.post(
        f"/api/tasks/{task_id}/plan",
        json={
            "instruction": "filter the uploaded peptide sequences",
            "api": {"api_key": TEST_API_KEY},
        },
    )
    assert rejected.status_code == 422
    assert_secret_absent(rejected.json())
    assert_secret_absent(rejected.text)
    assert_secret_absent(planned.json())
    assert_secret_absent(planned.text)


def test_about_returns_the_pinned_tool_manifest(tmp_path):
    client, _ = make_client(tmp_path, lambda request: httpx.Response(500))

    response = client.get("/api/about")

    assert response.status_code == 200
    assert response.json() == {
        "version": "0.2.0",
        "github_url": "https://github.com/Verture-Liu/2026summerproject",
        "tools": [
            {"id": "fastqc", "version": "0.12.1"},
            {"id": "multiqc", "version": "1.35"},
            {"id": "seqkit", "version": "2.13.0"},
            {"id": "seqtk", "version": "1.5-r133"},
            {"id": "samtools", "version": "1.23.1"},
            {"id": "bwa", "version": "0.7.19-r1273"},
            {"id": "bowtie2", "version": "2.5.5"},
        ],
    }

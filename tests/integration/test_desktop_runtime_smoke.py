from fastapi.testclient import TestClient

from research_agent.main import create_app
from research_agent.runtime.configuration import RuntimeConfiguration
from research_agent.runtime.paths import resource_root
from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secrets import MemorySecretStore


def test_tokenized_desktop_runtime_protects_api_and_serves_packaged_resources(tmp_path):
    configuration = RuntimeConfiguration(
        JsonPreferences(tmp_path / "preferences.json"),
        MemorySecretStore(),
    )
    client = TestClient(
        create_app(
            task_root=tmp_path / "tasks",
            runtime_configuration=configuration,
            session_token="desktop-smoke-token",
        )
    )
    headers = {"X-PaleoRigor-Token": "desktop-smoke-token"}

    assert client.get("/api/health").status_code == 401
    assert client.get("/api/health", headers=headers).json()["status"] == "ok"
    assert client.get("/api/config", headers=headers).json()["api_key_present"] is False
    about = client.get("/api/about", headers=headers)
    assert about.status_code == 200
    assert len(about.json()["tools"]) == 7
    assert (resource_root() / "resources" / "tool_manifest.json").is_file()

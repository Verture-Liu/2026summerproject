from pathlib import Path

from research_agent.config import Settings
from research_agent.runtime.configuration import RuntimeApiConfig


def test_settings_load_openai_compatible_fields():
    settings = Settings.load(
        {
            "AGENT_API_BASE_URL": "https://example.test/v1",
            "AGENT_API_KEY": "secret",
            "AGENT_MODEL": "model-a",
        }
    )
    assert settings.api_base_url == "https://example.test/v1"
    assert settings.model == "model-a"


def test_settings_redacts_api_key():
    settings = Settings.load({"AGENT_API_KEY": "secret"})
    assert settings.redacted()["api_key"] == "***"


def test_settings_from_runtime_uses_the_runtime_api_configuration():
    settings = Settings.from_runtime(
        RuntimeApiConfig(
            base_url="https://api.deepseek.com",
            model="deepseek-v4-flash",
            api_key="runtime-secret",
        ),
        Path("/tmp/runtime-tasks"),
    )

    assert settings.api_base_url == "https://api.deepseek.com"
    assert settings.model == "deepseek-v4-flash"
    assert settings.api_key == "runtime-secret"
    assert settings.task_root == "/tmp/runtime-tasks"

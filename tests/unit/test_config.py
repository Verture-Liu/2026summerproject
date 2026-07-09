from research_agent.config import Settings


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

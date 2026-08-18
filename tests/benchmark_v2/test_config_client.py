import json

import httpx

from analysis.benchmark_v2.client import DeepSeekClient
from analysis.benchmark_v2.config import load_config


def test_config_loads_env_without_exposing_secret(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "AGENT_API_BASE_URL=https://api.deepseek.com\n"
        "AGENT_API_KEY=top-secret\n"
        "AGENT_MODEL=deepseek-v4-flash\n",
        encoding="utf-8",
    )
    config = load_config(env_path)
    assert config.api_key == "top-secret"
    redacted = json.dumps(config.redacted())
    assert "top-secret" not in redacted
    assert config.redacted()["api_key_present"] is True


def test_client_uses_same_frozen_model_and_thinking_mode():
    seen = {}

    def handler(request: httpx.Request):
        seen.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "deepseek-v4-flash",
                "choices": [{"message": {"content": "{\"status\":\"blocked\",\"reason_code\":\"missing_mate\",\"message\":\"missing\"}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        client = DeepSeekClient(http, "https://api.deepseek.com", "secret", "deepseek-v4-flash", 30, 0)
        result = client.complete([{"role": "user", "content": "test"}])
    assert seen["model"] == "deepseek-v4-flash"
    assert seen["thinking"] == {"type": "enabled"}
    assert seen["response_format"] == {"type": "json_object"}
    assert result.usage["total_tokens"] == 15

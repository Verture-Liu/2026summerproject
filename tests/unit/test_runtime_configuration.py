import json
from collections.abc import Mapping

import pytest

from research_agent.runtime.configuration import RuntimeApiConfig, RuntimeConfiguration
from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secrets import MemorySecretStore


TEST_API_KEY = "task-3-test-api-key"
OLD_API_KEY = "task-3-old-api-key"
NEW_API_KEY = "task-3-new-api-key"


def make_configuration(tmp_path, store=None):
    return RuntimeConfiguration(
        JsonPreferences(tmp_path / "preferences.json"),
        MemorySecretStore() if store is None else store,
    )


def assert_secret_absent(value):
    if isinstance(value, Mapping):
        for nested_value in value.values():
            assert_secret_absent(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            assert_secret_absent(nested_value)
    elif isinstance(value, str):
        assert TEST_API_KEY not in value


def test_get_uses_deepseek_defaults_without_an_api_key(tmp_path):
    config = make_configuration(tmp_path)

    assert config.get() == RuntimeApiConfig(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
        api_key="",
    )


def test_get_reloads_preferences_and_retrieves_key_from_secret_store(tmp_path):
    preferences = JsonPreferences(tmp_path / "preferences.json")
    preferences.save(
        {
            "api_base_url": "https://initial.example/v1",
            "model": "initial-model",
            "language": "zh",
        }
    )
    store = MemorySecretStore()
    config = RuntimeConfiguration(preferences, store)

    assert config.get() == RuntimeApiConfig(
        base_url="https://initial.example/v1",
        model="initial-model",
        api_key="",
    )

    preferences.save(
        {
            "api_base_url": "https://updated.example/v1",
            "model": "updated-model",
            "language": "zh",
        }
    )
    store.set("api_key", TEST_API_KEY)

    assert config.get() == RuntimeApiConfig(
        base_url="https://updated.example/v1",
        model="updated-model",
        api_key=TEST_API_KEY,
    )


def test_update_replaces_an_existing_key_and_returns_a_redacted_response(tmp_path):
    preferences_path = tmp_path / "preferences.json"
    preferences = JsonPreferences(preferences_path)
    preferences.save({"language": "zh"})
    store = MemorySecretStore()
    store.set("api_key", OLD_API_KEY)
    config = RuntimeConfiguration(preferences, store)

    response = config.update(
        "  https://example.test/v1  ",
        "  model-a  ",
        f"  {NEW_API_KEY}  ",
    )

    assert config.get() == RuntimeApiConfig(
        base_url="https://example.test/v1",
        model="model-a",
        api_key=NEW_API_KEY,
    )
    assert store.get("api_key") == NEW_API_KEY
    assert store.get("api_key") != OLD_API_KEY
    assert json.loads(preferences_path.read_text(encoding="utf-8")) == {
        "api_base_url": "https://example.test/v1",
        "model": "model-a",
        "language": "zh",
    }
    assert response == {
        "base_url": "https://example.test/v1",
        "model": "model-a",
        "api_key_present": True,
    }
    assert_secret_absent(response)
    assert_secret_absent(json.dumps(response))


def test_update_keeps_the_existing_key_when_key_is_not_supplied(tmp_path):
    store = MemorySecretStore()
    store.set("api_key", TEST_API_KEY)
    config = make_configuration(tmp_path, store)

    response = config.update("https://example.test", "model-a", None)

    assert config.get().api_key == TEST_API_KEY
    assert response["api_key_present"] is True
    assert_secret_absent(response)
    assert_secret_absent(json.dumps(response))


def test_delete_api_key_removes_the_stored_key(tmp_path):
    store = MemorySecretStore()
    store.set("api_key", TEST_API_KEY)
    config = make_configuration(tmp_path, store)

    config.delete_api_key()

    assert config.get().api_key == ""


@pytest.mark.parametrize("base_url", ["ftp://example.test", "example.test", "https://"])
def test_update_rejects_non_http_base_urls(tmp_path, base_url):
    config = make_configuration(tmp_path)

    with pytest.raises(ValueError):
        config.update(base_url, "model-a", None)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://user@example.test/v1",
        "https://user:password@example.test/v1",
        "https://example.test/v1?api_key=secret",
        "https://example.test/v1#access-token",
        "https://example.test/v1?",
        "https://example.test/v1#",
    ],
)
def test_update_rejects_userinfo_query_and_fragment_without_persisting_them(
    tmp_path, base_url
):
    config = make_configuration(tmp_path)

    with pytest.raises(ValueError):
        config.update(base_url, "model-a", None)

    preferences_path = tmp_path / "preferences.json"
    assert not preferences_path.exists()
    assert base_url not in repr(config.get())


def test_get_scrubs_a_legacy_credential_bearing_base_url(tmp_path):
    preferences_path = tmp_path / "preferences.json"
    preferences = JsonPreferences(preferences_path)
    credentials = "legacy-user:legacy-password"
    preferences.save(
        {
            "api_base_url": f"https://{credentials}@example.test/v1",
            "model": "model-a",
        }
    )
    config = RuntimeConfiguration(preferences, MemorySecretStore())

    current = config.get()

    assert current.base_url == "https://api.deepseek.com"
    assert credentials not in repr(current)
    assert credentials not in preferences_path.read_text(encoding="utf-8")


def test_update_rejects_an_empty_model_after_whitespace_is_removed(tmp_path):
    config = make_configuration(tmp_path)

    with pytest.raises(ValueError):
        config.update("https://example.test", "   ", None)


class FailingSetSecretStore(MemorySecretStore):
    def set(self, name, value):
        raise RuntimeError("secret store unavailable")


def test_update_keeps_old_preferences_when_secret_store_set_fails(tmp_path):
    preferences = JsonPreferences(tmp_path / "preferences.json")
    preferences.save(
        {"api_base_url": "https://old.example/v1", "model": "old-model"}
    )
    secrets = FailingSetSecretStore()
    MemorySecretStore.set(secrets, "api_key", "old-secret")
    configuration = RuntimeConfiguration(preferences, secrets)

    with pytest.raises(RuntimeError, match="secret store unavailable"):
        configuration.update(
            "https://new.example/v1",
            "new-model",
            "new-secret",
        )

    assert preferences.load() == {
        "api_base_url": "https://old.example/v1",
        "model": "old-model",
    }
    assert configuration.get().api_key == "old-secret"


class FailAfterSavingOncePreferences(JsonPreferences):
    def __init__(self, path):
        super().__init__(path)
        self.fail_next_save = False

    def save(self, values):
        super().save(values)
        if self.fail_next_save:
            self.fail_next_save = False
            raise OSError("preference commit failed")


def test_update_rolls_back_key_and_preferences_when_preference_commit_fails(tmp_path):
    preferences = FailAfterSavingOncePreferences(tmp_path / "preferences.json")
    preferences.save(
        {"api_base_url": "https://old.example/v1", "model": "old-model"}
    )
    secrets = MemorySecretStore()
    secrets.set("api_key", "old-secret")
    configuration = RuntimeConfiguration(preferences, secrets)
    preferences.fail_next_save = True

    with pytest.raises(OSError, match="preference commit failed"):
        configuration.update(
            "https://new.example/v1",
            "new-model",
            "new-secret",
        )

    assert preferences.load() == {
        "api_base_url": "https://old.example/v1",
        "model": "old-model",
    }
    assert configuration.get().api_key == "old-secret"

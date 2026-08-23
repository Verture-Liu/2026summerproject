import json

from research_agent.runtime.preferences import JsonPreferences


def test_preferences_save_uses_only_supported_values_and_loads_them(tmp_path):
    path = tmp_path / "support" / "preferences.json"
    preferences = JsonPreferences(path)

    preferences.save(
        {
            "api_base_url": "https://example.test/v1",
            "model": "research-model",
            "language": "en",
            "api_key": "fixture-secret",
        }
    )

    assert json.loads(path.read_text()) == {
        "api_base_url": "https://example.test/v1",
        "model": "research-model",
        "language": "en",
    }
    assert preferences.load() == {
        "api_base_url": "https://example.test/v1",
        "model": "research-model",
        "language": "en",
    }


def test_preferences_save_replaces_file_via_sibling_temporary_file(tmp_path, monkeypatch):
    path = tmp_path / "preferences.json"
    preferences = JsonPreferences(path)
    replaced = []
    real_replace = __import__("os").replace

    def record_replace(source, destination):
        replaced.append((source, destination))
        real_replace(source, destination)

    monkeypatch.setattr("research_agent.runtime.preferences.os.replace", record_replace)

    preferences.save({"model": "research-model"})

    assert replaced == [(replaced[0][0], path)]
    assert replaced[0][0].parent == path.parent


def test_preferences_save_removes_temporary_file_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / "preferences.json"
    preferences = JsonPreferences(path)
    temporary_paths = []

    def fail_replace(source, destination):
        temporary_paths.append(source)
        raise OSError("replace failed")

    monkeypatch.setattr("research_agent.runtime.preferences.os.replace", fail_replace)

    try:
        preferences.save({"model": "research-model"})
    except OSError:
        pass
    else:
        raise AssertionError("preferences.save() should propagate replace failure")

    assert temporary_paths
    assert not temporary_paths[0].exists()

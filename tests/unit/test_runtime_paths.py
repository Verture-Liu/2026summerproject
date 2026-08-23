import sys
from pathlib import Path

from research_agent.runtime.paths import AppPaths, is_packaged_runtime, resource_root


def test_app_paths_use_macos_user_directories(tmp_path):
    paths = AppPaths.for_runtime(home=tmp_path, env={})
    assert paths.support_dir == tmp_path / "Library/Application Support/PaleoRigor"
    assert paths.preferences_file == paths.support_dir / "preferences.json"
    assert paths.task_root == tmp_path / "Library/Caches/PaleoRigor/tasks"
    assert paths.log_dir == tmp_path / "Library/Logs/PaleoRigor"


def test_app_paths_allow_isolated_test_root(tmp_path):
    paths = AppPaths.for_runtime(home=tmp_path, env={"PALEORIGOR_DATA_ROOT": str(tmp_path / "isolated")})
    assert paths.support_dir == tmp_path / "isolated/support"
    assert paths.task_root == tmp_path / "isolated/cache/tasks"


def test_source_resource_root_contains_web_assets():
    assert (resource_root() / "web/index.html").is_file()


def test_resource_root_uses_simulated_meipass_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "pyinstaller"
    packaged_resources = bundle / "research_agent"
    packaged_resources.mkdir(parents=True)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)

    assert resource_root() == packaged_resources
    assert is_packaged_runtime() is True


def test_packaged_runtime_explicit_override_wins_over_frozen_inference(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert is_packaged_runtime() is True
    assert is_packaged_runtime(False) is False

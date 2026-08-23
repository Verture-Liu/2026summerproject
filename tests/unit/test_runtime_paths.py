from pathlib import Path

from research_agent.runtime.paths import AppPaths, resource_root


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

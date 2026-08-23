import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/macos"


def test_build_configuration_is_apple_silicon_only():
    config = json.loads((PACKAGING / "build_config.json").read_text())
    assert config == {
        "app_name": "PaleoRigor",
        "bundle_identifier": "org.paleorigor.app",
        "version": "0.2.0-dev",
        "architecture": "arm64",
        "minimum_macos": "13.0",
        "backend_relative_path": "Contents/Resources/backend/PaleoRigorBackend",
        "tool_root_relative_path": "Contents/Resources/backend/_internal/research_agent/tools",
        "launcher_relative_path": "Contents/MacOS/PaleoRigor",
    }


def test_tool_sources_match_pinned_manifest_and_contain_no_credentials():
    sources = json.loads((PACKAGING / "tool-sources.json").read_text())
    manifest = json.loads((ROOT / "src/research_agent/resources/tool_manifest.json").read_text())
    pinned = {item["id"]: item["version"] for item in manifest["tools"]}
    assert {name: value["version"] for name, value in sources.items() if name != "java"} == pinned
    serialized = json.dumps(sources)
    assert "api_key" not in serialized.lower()
    assert "token" not in serialized.lower()
    assert all(value["upstream"].startswith("https://") for value in sources.values())


def test_all_declared_sources_exist_on_build_machine():
    sources = json.loads((PACKAGING / "tool-sources.json").read_text())
    missing = [value["source"] for value in sources.values() if not Path(value["source"]).exists()]
    assert missing == []

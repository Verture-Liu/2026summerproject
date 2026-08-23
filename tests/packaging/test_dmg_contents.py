import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/macos"


def _load_smoke_module():
    path = PACKAGING / "scripts/smoke_app.py"
    spec = importlib.util.spec_from_file_location("smoke_app", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dmg_builder_uses_compressed_read_only_image_and_applications_link():
    text = (PACKAGING / "scripts/create_dmg.sh").read_text()
    assert "hdiutil create" in text
    assert "-format UDZO" in text
    assert "/Applications" in text
    assert "PaleoRigor.app" in text


def test_smoke_runner_never_passes_token_on_command_line():
    smoke = _load_smoke_module()
    command = smoke.backend_command(
        Path("/Applications/PaleoRigor.app/Contents/Resources/backend/PaleoRigorBackend"),
        54321,
        Path("/tmp/private-token-file"),
    )
    assert "--session-token-file" in command
    assert "/tmp/private-token-file" in command
    assert "phase2-secret" not in command
    assert "--session-token" not in command


def test_release_scan_patterns_cover_credentials_and_developer_paths():
    smoke = _load_smoke_module()
    patterns = smoke.FORBIDDEN_BUNDLE_NAMES
    assert ".env" in patterns
    assert "__pycache__" in patterns
    assert ".DS_Store" in patterns
    assert smoke.DEVELOPER_PATH_MARKERS == (b"/Users/tianaoliu/Documents/vscode/2026summerproject",)

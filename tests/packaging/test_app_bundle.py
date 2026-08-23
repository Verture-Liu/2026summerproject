import importlib.util
import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/macos"


def _load_assembler():
    path = PACKAGING / "scripts/assemble_app.py"
    spec = importlib.util.spec_from_file_location("assemble_app", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_info_plist_declares_native_apple_silicon_application():
    with (PACKAGING / "Info.plist").open("rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleExecutable"] == "PaleoRigor"
    assert info["CFBundleIdentifier"] == "org.paleorigor.app"
    assert info["CFBundleShortVersionString"] == "0.2.0"
    assert info["LSMinimumSystemVersion"] == "13.0"
    assert info["LSArchitecturePriority"] == ["arm64"]
    assert info["LSUIElement"] is False
    assert info["NSHighResolutionCapable"] is True


def test_assembler_creates_expected_bundle_layout(tmp_path):
    assembler = _load_assembler()
    launcher = tmp_path / "launcher"
    launcher.write_bytes(b"launcher")
    launcher.chmod(0o755)
    backend = tmp_path / "backend-source"
    backend.mkdir()
    (backend / "PaleoRigorBackend").write_bytes(b"backend")
    (backend / "PaleoRigorBackend").chmod(0o755)
    (backend / "_internal").mkdir()
    (backend / "_internal/example").write_text("resource")
    cache = backend / "_internal/__pycache__"
    cache.mkdir()
    (cache / "example.pyc").write_bytes(b"developer cache")
    destination = tmp_path / "PaleoRigor.app"

    assembler.assemble(destination, launcher, backend, PACKAGING / "Info.plist")

    assert (destination / "Contents/MacOS/PaleoRigor").stat().st_mode & 0o111
    assert (destination / "Contents/Resources/backend/PaleoRigorBackend").stat().st_mode & 0o111
    assert (destination / "Contents/Resources/backend/_internal/example").read_text() == "resource"
    assert not (destination / "Contents/Resources/backend/_internal/__pycache__").exists()
    assert (destination / "Contents/Frameworks").is_dir()
    assert (destination / "Contents/Info.plist").is_file()


def test_development_signer_verifies_strict_bundle_signature():
    text = (PACKAGING / "scripts/sign_development.sh").read_text()
    assert "codesign --force --sign -" in text
    assert "codesign --verify --deep --strict" in text

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "packaging/windows/scripts/stage_tools.py"


def load_module():
    spec = importlib.util.spec_from_file_location("windows_stage_tools", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_safe_extract_zip_rejects_parent_traversal(tmp_path):
    module = load_module()
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape.exe", b"bad")

    with pytest.raises(ValueError, match="unsafe archive member"):
        module.safe_extract_zip(archive, tmp_path / "output")

    assert not (tmp_path / "escape.exe").exists()


def test_stage_from_cache_verifies_archives_and_creates_normalized_commands(tmp_path):
    module = load_module()
    cache = tmp_path / "cache"
    downloads = cache / "downloads"
    downloads.mkdir(parents=True)
    archive = downloads / "tiny.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("tiny/bin/tiny.exe", b"MZ-fixture")

    manifest = {
        "tools": {
            "tiny": {
                "version": "1.0",
                "strategy": "archive",
                "archive": archive.name,
                "url": "https://example.invalid/tiny.zip",
                "sha256": digest(archive),
                "command": "tiny.exe",
            }
        },
        "runtimes": {},
    }

    tool_root = module.stage_from_cache(cache, tmp_path / "staged", manifest)

    assert (tool_root / "components/tiny/tiny/bin/tiny.exe").read_bytes() == b"MZ-fixture"
    assert (tool_root / "bin/tiny.cmd").is_file()
    staged_manifest = json.loads((tool_root / "manifest.json").read_text())
    assert staged_manifest["tools"][0]["id"] == "tiny"
    assert staged_manifest["tools"][0]["command"] == "bin/tiny.cmd"


def test_stage_from_cache_requires_prebuilt_source_components(tmp_path):
    module = load_module()
    manifest = {
        "tools": {
            "seqtk": {
                "version": "1.5",
                "strategy": "msys2-source",
                "archive": "seqtk.tar.gz",
                "url": "https://example.invalid/seqtk.tar.gz",
                "sha256": "0" * 64,
                "command": "seqtk.exe",
            }
        },
        "runtimes": {},
    }

    with pytest.raises(FileNotFoundError, match="prebuilt component.*seqtk"):
        module.stage_from_cache(tmp_path / "cache", tmp_path / "staged", manifest)


def test_stage_from_cache_rejects_checksum_mismatch(tmp_path):
    module = load_module()
    downloads = tmp_path / "cache/downloads"
    downloads.mkdir(parents=True)
    (downloads / "tiny.zip").write_bytes(b"not the declared archive")
    manifest = {
        "tools": {
            "tiny": {
                "version": "1.0",
                "strategy": "archive",
                "archive": "tiny.zip",
                "url": "https://example.invalid/tiny.zip",
                "sha256": "0" * 64,
                "command": "tiny.exe",
            }
        },
        "runtimes": {},
    }

    with pytest.raises(ValueError, match="checksum mismatch.*tiny"):
        module.stage_from_cache(tmp_path / "cache", tmp_path / "staged", manifest)

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/macos"
TOOLS = ("fastqc", "multiqc", "seqkit", "seqtk", "samtools", "bwa", "bowtie2")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_manifest_exposes_upstream_and_license_for_every_tool():
    manifest = json.loads((ROOT / "src/research_agent/resources/tool_manifest.json").read_text())
    entries = {item["id"]: item for item in manifest["tools"]}
    assert tuple(entries) == TOOLS
    for tool in TOOLS:
        assert entries[tool]["command"] == f"bin/{tool}"
        assert entries[tool]["upstream"].startswith("https://")
        assert entries[tool]["license_file"] == f"licenses/{tool}.txt"


def test_packaging_has_license_inventory_for_every_tool():
    license_dir = PACKAGING / "licenses"
    readme = (license_dir / "README.md").read_text()
    for tool in TOOLS:
        license_text = (license_dir / f"{tool}.txt").read_text()
        assert tool.casefold() in readme.casefold()
        assert len(license_text.strip()) >= 40


def test_stage_tool_helpers_create_relative_executable_links(tmp_path):
    stage = _load_module("stage_tools", PACKAGING / "scripts/stage_tools.py")
    target = tmp_path / "tools"
    executable = target / "components/example/bin/example"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"binary")
    executable.chmod(0o755)

    link = stage.create_command_link(target, "example", "components/example/bin/example")

    assert link.is_symlink()
    assert link.readlink() == Path("../components/example/bin/example")
    assert link.resolve() == executable


def test_macho_validator_allows_only_system_absolute_dependencies():
    verify = _load_module("verify_macho", PACKAGING / "scripts/verify_macho.py")
    assert verify.is_allowed_dependency("/usr/lib/libz.1.dylib")
    assert verify.is_allowed_dependency("/System/Library/Frameworks/AppKit.framework/AppKit")
    assert verify.is_allowed_dependency("@loader_path/../lib/libhts.3.dylib")
    assert verify.is_allowed_dependency("@rpath/libz.1.dylib")
    assert not verify.is_allowed_dependency("/opt/miniconda3/lib/libz.1.dylib")
    assert not verify.is_allowed_dependency("/opt/homebrew/lib/libzstd.1.dylib")


def test_stager_recognises_bundleable_conda_dependencies():
    stage = _load_module("stage_tools_dependency", PACKAGING / "scripts/stage_tools.py")
    source_lib = Path("/opt/miniconda3/envs/example/lib")
    assert stage.bundleable_dependency_name("@rpath/libz.1.dylib", source_lib) == "libz.1.dylib"
    assert stage.bundleable_dependency_name(
        "/opt/miniconda3/envs/example/lib/libtinfow.6.dylib", source_lib
    ) == "libtinfow.6.dylib"
    assert stage.bundleable_dependency_name("/usr/lib/libSystem.B.dylib", source_lib) is None


def test_multiqc_entry_uses_official_cli_entrypoint():
    text = (PACKAGING / "multiqc_entry.py").read_text()
    assert "from multiqc.__main__ import run_multiqc" in text
    assert "run_multiqc()" in text

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/windows"
EXPECTED_TOOLS = {"fastqc", "multiqc", "seqkit", "seqtk", "samtools", "bwa", "bowtie2"}


def test_windows_build_configuration_is_x64_and_isolated_from_macos():
    config = json.loads((PACKAGING / "build_config.json").read_text())

    assert config["app_name"] == "PaleoRigor"
    assert config["version"] == "0.2.0-dev"
    assert config["architecture"] == "x64"
    assert config["minimum_windows"] == "10"
    assert config["backend_relative_path"] == "backend/PaleoRigorBackend.exe"
    assert config["tool_root_relative_path"] == "tools"
    assert config["launcher_relative_path"] == "PaleoRigor.exe"
    assert (ROOT / "packaging/macos/build_config.json").is_file()


def test_windows_sources_pin_all_tools_and_runtime_with_real_checksums():
    sources = json.loads((PACKAGING / "tool-sources.json").read_text())

    assert set(sources["tools"]) == EXPECTED_TOOLS
    assert set(sources["runtimes"]) == {"java"}
    for group in (sources["tools"], sources["runtimes"]):
        for name, item in group.items():
            assert item["url"].startswith("https://"), name
            assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"]), name
            assert item["archive"], name
            assert item["strategy"] in {"archive", "python-wheel", "msys2-source"}, name


def test_windows_manifests_contain_no_credentials_or_local_machine_paths():
    serialized = (PACKAGING / "tool-sources.json").read_text()

    assert not re.search(r"api[_-]?key|password|bearer|token", serialized, re.IGNORECASE)
    assert "/Users/" not in serialized
    assert "C:\\Users\\" not in serialized


def test_windows_third_party_notice_names_every_bundled_tool():
    notice = (PACKAGING / "licenses/README.md").read_text().lower()

    for tool in EXPECTED_TOOLS:
        assert tool in notice

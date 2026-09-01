from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/windows"


def test_inno_setup_installs_per_user_with_shortcuts_and_uninstaller():
    source = (PACKAGING / "installer/PaleoRigor.iss").read_text()

    assert "PrivilegesRequired=lowest" in source
    assert "DefaultDirName={localappdata}\\Programs\\PaleoRigor" in source
    assert "OutputBaseFilename=PaleoRigor-Setup" in source
    assert "ArchitecturesAllowed=x64compatible" in source
    assert 'Name: "{group}\\PaleoRigor"' in source
    assert 'Name: "{autodesktop}\\PaleoRigor"' in source
    assert "Uninstallable=yes" in source
    assert "PaleoRigor.exe" in source
    assert "download" not in source.lower()


def test_build_script_downloads_with_checksums_and_builds_all_layers():
    source = (PACKAGING / "scripts/build.ps1").read_text()

    assert "Get-FileHash" in source
    assert "tool-sources.json" in source
    assert "PyInstaller" in source
    assert "dotnet publish" in source
    assert "stage_tools.py" in source
    assert "ISCC.exe" in source
    assert "PaleoRigor-Setup.exe" in source
    assert "PALEORIGOR_API_KEY" not in source


def test_build_script_fails_at_the_native_command_that_breaks():
    source = (PACKAGING / "scripts/build.ps1").read_text()

    assert "Invoke-Native" in source
    assert "$LASTEXITCODE" in source
    assert "::error::" in source
    assert "windows-build-stage.txt" in source
    assert '$ErrorActionPreference = "Continue"' in source
    assert "$PreviousErrorActionPreference" in source


def test_msys2_script_builds_three_missing_native_tools_from_pinned_sources():
    source = (PACKAGING / "scripts/build_msys2_tools.sh").read_text()

    for tool in ("seqtk", "samtools", "bwa"):
        assert tool in source
    assert "set -euo pipefail" in source
    assert "C:/msys64" not in source


def test_seqtk_build_supplies_mingw_posix_random_compatibility():
    source = (PACKAGING / "scripts/build_msys2_tools.sh").read_text()
    header = PACKAGING / "scripts/seqtk_mingw_compat.h"

    assert "seqtk_mingw_compat.h" in source
    assert "-include seqtk_mingw_compat.h" in source
    assert header.is_file()
    text = header.read_text()
    for function in ("drand48", "srand48", "lrand48"):
        assert function in text


def test_smoke_script_produces_verification_and_checksum_files():
    source = (PACKAGING / "scripts/smoke_test.ps1").read_text()

    assert "verification.json" in source
    assert "SHA256SUMS.txt" in source
    assert "Get-FileHash" in source
    assert "PaleoRigor-Setup.exe" in source
    assert "seven_tools" in source
    assert "backend_health" in source
    assert "uninstall" in source

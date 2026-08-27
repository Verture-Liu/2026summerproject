from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_windows_readme_explains_build_test_and_unsigned_limitations():
    text = (ROOT / "packaging/windows/README.md").read_text()

    for phrase in (
        "Windows 10/11 x64",
        "Python 3.13",
        ".NET 8 SDK",
        "MSYS2",
        "Inno Setup 6",
        "build.ps1",
        "smoke_test.ps1",
        "SmartScreen",
        "research prototype",
    ):
        assert phrase in text
    for tool in ("FastQC", "MultiQC", "SeqKit", "SeqTk", "Samtools", "BWA", "Bowtie2"):
        assert tool in text


def test_public_download_readme_retains_macos_and_describes_windows_separately():
    text = (ROOT / "paleorigor/README.md").read_text()

    assert "PaleoRigor-dev-arm64.dmg" in text
    assert "PaleoRigor-Setup.exe" in text
    assert "Apple Silicon" in text
    assert "Windows 10/11 x64" in text
    assert "Windows Credential Manager" in text


def test_windows_ci_builds_without_publishing_an_unverified_release():
    workflow = (ROOT / ".github/workflows/windows-build.yml").read_text()

    assert "windows-latest" in workflow
    assert "msys2/setup-msys2" in workflow
    assert "actions/setup-python" in workflow
    assert "actions/setup-dotnet" in workflow
    assert "build.ps1" in workflow
    assert "smoke_test.ps1" in workflow
    assert "actions/upload-artifact" in workflow
    assert "softprops/action-gh-release" not in workflow
    assert "contents: write" not in workflow

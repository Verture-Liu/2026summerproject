from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging/windows"


def test_windows_backend_entry_reuses_hardened_shared_launcher():
    entry = (PACKAGING / "backend_entry.py").read_text()
    spec = (PACKAGING / "backend.spec").read_text()

    assert "from research_agent.launcher import main" in entry
    assert "PaleoRigorBackend" in spec
    assert "research_agent/web" in spec
    assert "research_agent/resources" in spec
    assert "research_agent/skill_packages" in spec
    assert "keyring.backends.Windows" in spec


def test_windows_launcher_uses_loopback_random_token_and_safe_arguments():
    source = (PACKAGING / "launcher/PaleoRigorLauncher.cs").read_text()

    assert "IPAddress.Loopback" in source
    assert "RandomNumberGenerator.GetBytes(32)" in source
    assert 'ArgumentList.Add("--session-token-file")' in source
    assert 'ArgumentList.Add("--no-browser")' in source
    assert 'UseShellExecute = false' in source
    assert "X-PaleoRigor-Token" in source
    assert "/api/health" in source
    assert "http://127.0.0.1:" in source


def test_windows_launcher_uses_local_app_data_and_cleans_up_process_and_token():
    source = (PACKAGING / "launcher/PaleoRigorLauncher.cs").read_text()

    assert "Environment.SpecialFolder.LocalApplicationData" in source
    assert "PALEORIGOR_TOOL_ROOT" in source
    assert "Kill(entireProcessTree: true)" in source
    assert "File.Delete(tokenFile)" in source
    assert "NotifyIcon" in source
    assert "PaleoRigor could not start" in source


def test_windows_launcher_project_builds_a_self_contained_winexe():
    project = (PACKAGING / "launcher/PaleoRigorLauncher.csproj").read_text()

    assert "<OutputType>WinExe</OutputType>" in project
    assert "<TargetFramework>net8.0-windows</TargetFramework>" in project
    assert "<RuntimeIdentifier>win-x64</RuntimeIdentifier>" in project
    assert "<SelfContained>true</SelfContained>" in project
    assert "<PublishSingleFile>true</PublishSingleFile>" in project

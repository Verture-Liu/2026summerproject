from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_backend_spec_is_arm64_onedir_and_collects_research_agent_data():
    text = (ROOT / "packaging/macos/backend.spec").read_text()
    assert 'target_arch="arm64"' in text
    assert "COLLECT(" in text
    assert 'collect_data_files("research_agent")' in text


def test_native_launcher_uses_token_file_and_authenticated_health():
    text = (ROOT / "packaging/macos/Launcher/main.m").read_text()
    assert '"--session-token-file"' in text
    assert "chmod(tokenFile.fileSystemRepresentation, 0600)" in text
    assert 'forHTTPHeaderField:@"X-PaleoRigor-Token"' in text
    assert "api/health" in text
    assert "127.0.0.1" in text
    assert "[[NSWorkspace sharedWorkspace] openURL:url]" in text

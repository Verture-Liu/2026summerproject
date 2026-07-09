import subprocess

from research_agent.files.native_dialog import choose_directory


def test_macos_directory_chooser_uses_osascript(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, "/Users/example/Results/\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    selected = choose_directory(system="Darwin")
    assert selected == "/Users/example/Results"
    assert captured["command"][0] == "/usr/bin/osascript"
    assert "choose folder" in captured["command"][2]
    assert "Choose a Research Agent results folder" in captured["command"][2]


def test_macos_directory_chooser_returns_empty_when_cancelled(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "User canceled.")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert choose_directory(system="Darwin") == ""

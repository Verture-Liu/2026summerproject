import platform
import shutil
import subprocess
from pathlib import Path


def _choose_macos() -> str:
    script = (
        'POSIX path of (choose folder with prompt '
        '"Choose a Research Agent results folder")'
    )
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip().rstrip("/")


def _choose_windows() -> str:
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
        "$dialog.Description = 'Choose a Research Agent results folder'; "
        "if ($dialog.ShowDialog() -eq 'OK') { $dialog.SelectedPath }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _choose_linux() -> str:
    zenity = shutil.which("zenity")
    if zenity is None:
        return ""
    result = subprocess.run(
        [zenity, "--file-selection", "--directory", "--title=Choose a Research Agent results folder"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def choose_directory(system: str | None = None) -> str:
    current = system or platform.system()
    if current == "Darwin":
        return _choose_macos()
    if current == "Windows":
        return _choose_windows()
    if current == "Linux":
        return _choose_linux()
    return ""

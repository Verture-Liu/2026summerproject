#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import secrets
import socket
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


FORBIDDEN_BUNDLE_NAMES = (".env", "__pycache__", ".DS_Store")
DEVELOPER_PATH_MARKERS = (b"/Users/tianaoliu/Documents/vscode/2026summerproject",)
EXPECTED_TOOLS = {
    "fastqc": "0.12.1",
    "multiqc": "1.35",
    "seqkit": "2.13.0",
    "seqtk": "1.5-r133",
    "samtools": "1.23.1",
    "bwa": "0.7.19-r1273",
    "bowtie2": "2.5.5",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def backend_command(backend: Path, port: int, token_file: Path) -> list[str]:
    return [
        str(backend),
        "--no-browser",
        "--port", str(port),
        "--session-token-file", str(token_file),
    ]


def request_json(url: str, token: str | None = None) -> tuple[int, dict]:
    request = urllib.request.Request(url)
    if token:
        request.add_header("X-PaleoRigor-Token", token)
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def wait_for_health(base_url: str, token: str, process: subprocess.Popen, timeout: float = 30) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Packaged backend exited with code {process.returncode}")
        try:
            status, payload = request_json(f"{base_url}/api/health", token)
            if status == 200:
                return payload
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise TimeoutError("Packaged backend did not become healthy")


def scan_bundle(app: Path) -> list[str]:
    errors: list[str] = []
    for path in app.rglob("*"):
        if path.name in FORBIDDEN_BUNDLE_NAMES:
            errors.append(f"forbidden bundle entry: {path}")
        if not path.is_file() or path.is_symlink():
            continue
        try:
            with path.open("rb") as handle:
                overlap = b""
                while block := handle.read(1024 * 1024):
                    sample = overlap + block
                    for marker in DEVELOPER_PATH_MARKERS:
                        if marker in sample:
                            errors.append(f"developer path marker in {path}")
                    overlap = sample[-128:]
        except OSError as error:
            errors.append(f"could not scan {path}: {error}")
    return sorted(set(errors))


def check_tool_commands(tool_root: Path) -> dict[str, bool]:
    checks = {
        "fastqc": (["--version"], "0.12.1"),
        "multiqc": (["--version"], "1.35"),
        "seqkit": (["version"], "2.13.0"),
        "seqtk": ([], "Usage:   seqtk"),
        "samtools": (["--version"], "1.23.1"),
        "bwa": ([], "0.7.19-r1273"),
        "bowtie2": (["--version"], "2.5.5"),
    }
    environment = {"HOME": "/tmp", "TMPDIR": "/tmp", "LANG": "en_US.UTF-8", "PATH": "/usr/bin:/bin"}
    results: dict[str, bool] = {}
    for name, (arguments, marker) in checks.items():
        completed = subprocess.run(
            [str(tool_root / "bin" / name), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        results[name] = marker in completed.stdout + completed.stderr
    return results


def run_smoke(app: Path, scan: bool = True) -> dict:
    app = app.resolve()
    backend = app / "Contents/Resources/backend/PaleoRigorBackend"
    tool_root = app / "Contents/Resources/backend/_internal/research_agent/tools"
    with tempfile.TemporaryDirectory(prefix="paleorigor-app-smoke-") as temporary:
        temporary_path = Path(temporary)
        token = secrets.token_urlsafe(32)
        token_file = temporary_path / "launch.token"
        token_file.write_text(token)
        token_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        port = free_port()
        environment = {
            "HOME": str(temporary_path),
            "TMPDIR": str(temporary_path),
            "LANG": "en_US.UTF-8",
            "PATH": "/usr/bin:/bin",
        }
        process = subprocess.Popen(
            backend_command(backend, port, token_file),
            cwd=temporary_path,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        base_url = f"http://127.0.0.1:{port}"
        try:
            health = wait_for_health(base_url, token, process)
            unauthorized, _ = request_json(f"{base_url}/api/health")
            about_status, about = request_json(f"{base_url}/api/about", token)
            config_status, config = request_json(f"{base_url}/api/config", token)
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        result = {
            "health": health,
            "unauthorized_status": unauthorized,
            "about_status": about_status,
            "about_tools": {item["id"]: item["version"] for item in about["tools"]},
            "config_status": config_status,
            "api_key_present": config["api_key_present"],
            "token_file_deleted": not token_file.exists(),
            "tool_commands": check_tool_commands(tool_root),
            "bundle_scan_errors": scan_bundle(app) if scan else [],
        }
        expected = {
            "health": {"status": "ok", "version": "0.2.0"},
            "unauthorized_status": 401,
            "about_status": 200,
            "about_tools": EXPECTED_TOOLS,
            "config_status": 200,
            "api_key_present": False,
            "token_file_deleted": True,
            "tool_commands": {name: True for name in EXPECTED_TOOLS},
            "bundle_scan_errors": [],
        }
        result["passed"] = all(result[key] == value for key, value in expected.items())
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=Path)
    parser.add_argument("--skip-scan", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_smoke(args.app, scan=not args.skip_scan)
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized)
    print(serialized, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

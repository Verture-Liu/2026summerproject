import argparse
import socket
import sys
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote

import uvicorn

from research_agent.main import create_app
from research_agent.runtime.configuration import RuntimeConfiguration
from research_agent.runtime.paths import AppPaths, is_packaged_runtime
from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secrets import secret_store_for_platform
from research_agent.runtime.session import generate_session_token


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket() as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the local Research Agent.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically.")
    parser.add_argument("--port", type=int, help="Use a fixed local port.")
    parser.add_argument(
        "--session-token-file",
        type=Path,
        help="Read the launch token from this mode-0600 file and delete it immediately.",
    )
    return parser


def build_browser_url(host: str, port: int, token: str) -> str:
    return f"http://{host}:{port}/#token={quote(token, safe='')}"


def read_session_token_file(path: Path, platform_name: str | None = None) -> str:
    try:
        platform_name = sys.platform if platform_name is None else platform_name
        if platform_name != "win32":
            mode = path.stat().st_mode & 0o777
            if mode & 0o077:
                raise ValueError("Session token file permissions are too broad")
        token = path.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("Session token file is empty")
        return token
    finally:
        path.unlink(missing_ok=True)


def build_runtime(session_token: str | None = None) -> tuple[AppPaths, RuntimeConfiguration, str]:
    paths = AppPaths.for_runtime()
    paths.ensure()
    configuration = RuntimeConfiguration(
        JsonPreferences(paths.preferences_file),
        secret_store_for_platform(sys.platform),
    )
    return paths, configuration, session_token or generate_session_token()


def launch(
    open_browser: bool = True,
    port: int | None = None,
    session_token: str | None = None,
) -> None:
    host = "127.0.0.1"
    port = port or find_free_port(host)
    paths, configuration, token = build_runtime(session_token=session_token)
    app = create_app(
        task_root=paths.task_root,
        runtime_configuration=configuration,
        session_token=token,
    )
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(build_browser_url(host, port, token))).start()
    kwargs = {"host": host, "port": port}
    if is_packaged_runtime():
        kwargs["log_config"] = None
    uvicorn.run(app, **kwargs)


def main() -> None:
    args = build_parser().parse_args()
    token = read_session_token_file(args.session_token_file) if args.session_token_file else None
    launch(open_browser=not args.no_browser, port=args.port, session_token=token)

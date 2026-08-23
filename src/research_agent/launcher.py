import argparse
import socket
import sys
import threading
import webbrowser
from urllib.parse import quote

import uvicorn

from research_agent.main import create_app
from research_agent.runtime.configuration import RuntimeConfiguration
from research_agent.runtime.paths import AppPaths
from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secrets import MacOSKeychainSecretStore
from research_agent.runtime.session import generate_session_token


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket() as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the local Research Agent.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically.")
    parser.add_argument("--port", type=int, help="Use a fixed local port.")
    return parser


def build_browser_url(host: str, port: int, token: str) -> str:
    return f"http://{host}:{port}/#token={quote(token, safe='')}"


def build_runtime() -> tuple[AppPaths, RuntimeConfiguration, str]:
    paths = AppPaths.for_runtime()
    paths.ensure()
    configuration = RuntimeConfiguration(
        JsonPreferences(paths.preferences_file),
        MacOSKeychainSecretStore(),
    )
    return paths, configuration, generate_session_token()


def launch(open_browser: bool = True, port: int | None = None) -> None:
    host = "127.0.0.1"
    port = port or find_free_port(host)
    paths, configuration, token = build_runtime()
    app = create_app(
        task_root=paths.task_root,
        runtime_configuration=configuration,
        session_token=token,
    )
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(build_browser_url(host, port, token))).start()
    kwargs = {"host": host, "port": port}
    if getattr(sys, "frozen", False):
        kwargs["log_config"] = None
    uvicorn.run(app, **kwargs)


def main() -> None:
    args = build_parser().parse_args()
    launch(open_browser=not args.no_browser, port=args.port)

import argparse
import socket
import threading
import webbrowser

import uvicorn


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket() as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the local Research Agent.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically.")
    parser.add_argument("--port", type=int, help="Use a fixed local port.")
    return parser


def launch(open_browser: bool = True, port: int | None = None) -> None:
    host = "127.0.0.1"
    port = port or find_free_port(host)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run("research_agent.main:app", host=host, port=port)


def main() -> None:
    args = build_parser().parse_args()
    launch(open_browser=not args.no_browser, port=args.port)

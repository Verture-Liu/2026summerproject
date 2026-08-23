from fastapi import FastAPI

from research_agent import launcher
from research_agent.runtime.paths import AppPaths
from research_agent.runtime.secrets import MacOSKeychainSecretStore


def test_find_free_port_returns_bindable_port():
    port = launcher.find_free_port()
    assert 1024 < port < 65536


def test_launcher_parser_supports_no_browser():
    args = launcher.build_parser().parse_args(
        ["--no-browser", "--port", "8123", "--session-token-file", "/tmp/token"]
    )
    assert args.no_browser is True
    assert args.port == 8123
    assert args.session_token_file.as_posix() == "/tmp/token"


def test_session_token_file_requires_private_permissions_and_is_deleted(tmp_path):
    token_file = tmp_path / "launch-token"
    token_file.write_text("fixed-token\n")
    token_file.chmod(0o600)

    assert launcher.read_session_token_file(token_file) == "fixed-token"
    assert not token_file.exists()


def test_session_token_file_with_broad_permissions_is_rejected_and_deleted(tmp_path):
    token_file = tmp_path / "launch-token"
    token_file.write_text("secret")
    token_file.chmod(0o644)

    try:
        launcher.read_session_token_file(token_file)
    except ValueError as exc:
        assert "permissions" in str(exc)
    else:
        raise AssertionError("Expected broad token-file permissions to be rejected")
    assert not token_file.exists()


def test_build_browser_url_places_an_encoded_token_in_a_fragment():
    url = launcher.build_browser_url("127.0.0.1", 8123, "token /?#%")

    assert url == "http://127.0.0.1:8123/#token=token%20%2F%3F%23%25"
    assert "?token=" not in url


def test_build_runtime_creates_app_directories_and_composes_keychain_configuration(tmp_path, monkeypatch):
    paths = AppPaths.for_runtime(home=tmp_path, env={})
    monkeypatch.setattr(
        launcher.AppPaths,
        "for_runtime",
        classmethod(lambda _cls: paths),
    )
    monkeypatch.setattr(launcher, "generate_session_token", lambda: "generated-token")

    runtime_paths, configuration, token = launcher.build_runtime()

    assert runtime_paths == paths
    assert token == "generated-token"
    assert isinstance(configuration._secret_store, MacOSKeychainSecretStore)
    assert all(
        directory.is_dir()
        for directory in [
            paths.support_dir,
            paths.task_root,
            paths.cache_dir,
            paths.log_dir,
            paths.installed_skill_root,
        ]
    )


def test_launch_passes_one_token_to_the_app_and_tokenized_browser_fragment(monkeypatch, tmp_path):
    paths = AppPaths.for_runtime(home=tmp_path, env={})
    configuration = object()
    app = FastAPI()
    browser_urls = []
    create_calls = []
    uvicorn_calls = []

    monkeypatch.setattr(
        launcher,
        "build_runtime",
        lambda session_token=None: (paths, configuration, session_token or "same token/?"),
    )
    monkeypatch.setattr(
        launcher,
        "create_app",
        lambda **kwargs: create_calls.append(kwargs) or app,
    )

    class ImmediateTimer:
        def __init__(self, _delay, callback):
            self.callback = callback

        def start(self):
            self.callback()

    monkeypatch.setattr(launcher.threading, "Timer", ImmediateTimer)
    monkeypatch.setattr(launcher.webbrowser, "open", browser_urls.append)
    monkeypatch.setattr(
        launcher.uvicorn,
        "run",
        lambda passed_app, **kwargs: uvicorn_calls.append((passed_app, kwargs)),
    )

    launcher.launch(port=8123)

    assert create_calls == [
        {
            "task_root": paths.task_root,
            "runtime_configuration": configuration,
            "session_token": "same token/?",
        }
    ]
    assert browser_urls == ["http://127.0.0.1:8123/#token=same%20token%2F%3F"]
    assert uvicorn_calls == [(app, {"host": "127.0.0.1", "port": 8123})]


def test_packaged_launcher_disables_uvicorn_logging_only_when_frozen(monkeypatch, tmp_path):
    paths = AppPaths.for_runtime(home=tmp_path, env={})
    app = FastAPI()
    calls = []
    monkeypatch.setattr(
        launcher,
        "build_runtime",
        lambda session_token=None: (paths, object(), session_token or "token"),
    )
    monkeypatch.setattr(launcher, "create_app", lambda **_kwargs: app)
    monkeypatch.setattr(launcher.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        launcher.uvicorn,
        "run",
        lambda passed_app, **kwargs: calls.append((passed_app, kwargs)),
    )

    launcher.launch(open_browser=False, port=8123)

    assert calls == [(app, {"host": "127.0.0.1", "port": 8123, "log_config": None})]

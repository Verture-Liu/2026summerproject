# PaleoRigor macOS Phase 1 Portable Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing PaleoRigor backend and browser interface portable, Keychain-backed, session-protected, and able to resolve the seven future bundled tools without relying on the repository layout, `.env`, Conda activation, Homebrew, or the user's `PATH` in packaged mode.

**Architecture:** Add a small runtime-services layer for application paths, preferences, secrets, session authentication, and bundled resources. Keep FastAPI and the browser UI, but move API credentials from each planning request into backend-managed configuration and require a per-launch token on every `/api/` request. Extend the current tool resolver so packaged tools take precedence while retaining PATH and Conda fallbacks for developer mode.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic 2, macOS `/usr/bin/security`, vanilla HTML/CSS/JavaScript, pytest, PyInstaller-compatible resource discovery.

## Global Constraints

- Target Apple Silicon Macs running macOS 13 Ventura or later.
- Bind the service only to `127.0.0.1`.
- Store API keys only in macOS Keychain; never write keys to `.env`, preferences, logs, records, workflow JSON, or HTTP responses.
- Send research-file summaries and natural-language instructions to the configured model API, but do not upload research-file contents to a PaleoRigor-controlled server.
- Preserve workflow review and explicit local-execution approval.
- Preserve the existing successful-result layout: `final_outputs/`, `step_outputs/`, and `PaleoRigor Records/`.
- The seven bundled tool identifiers are `fastqc`, `multiqc`, `seqkit`, `seqtk`, `samtools`, `bwa`, and `bowtie2`.
- Pinned tool versions are FastQC 0.12.1, MultiQC 1.35, SeqKit 2.13.0, SeqTk 1.5-r133, Samtools 1.23.1, BWA 0.7.19-r1273, and Bowtie2 2.5.5.
- Phase 1 must not download tools, build `.app`, sign code, create a DMG, or modify unrelated manuscript and benchmark artifacts.

---

## File Structure

### Files created

- `pyproject.toml` — authoritative Python package metadata, dependencies, console entry point, and package-data rules.
- `src/research_agent/runtime/__init__.py` — runtime-services package marker.
- `src/research_agent/runtime/paths.py` — packaged/source resource discovery and macOS writable application paths.
- `src/research_agent/runtime/preferences.py` — non-secret JSON preferences with atomic writes.
- `src/research_agent/runtime/secrets.py` — secret-store protocol, macOS Keychain adapter, and in-memory test adapter.
- `src/research_agent/runtime/configuration.py` — redacted model configuration service combining preferences and Keychain.
- `src/research_agent/runtime/session.py` — launch-token generation and FastAPI API-route protection.
- `src/research_agent/resources/tool_manifest.json` — seven-tool names, pinned versions, and future bundle-relative commands.
- `tests/unit/test_runtime_paths.py` — source/packaged/writable path tests.
- `tests/unit/test_preferences.py` — atomic preference persistence tests.
- `tests/unit/test_secrets.py` — Keychain command and redaction tests.
- `tests/unit/test_runtime_configuration.py` — configuration-service tests.
- `tests/unit/test_session_auth.py` — API token acceptance/rejection tests.
- `tests/integration/test_runtime_config_api.py` — first-run configuration and planning-with-stored-key tests.

### Files modified

- `src/research_agent/config.py` — retain environment compatibility but delegate desktop settings to the runtime configuration service.
- `src/research_agent/main.py` — inject runtime services, add configuration/about/health endpoints, remove API keys from `PlanRequest`, and apply API token middleware.
- `src/research_agent/launcher.py` — generate a token, use application paths, pass injected runtime state, and place the token in the browser URL fragment.
- `src/research_agent/skills/conda_tools.py` — resolve bundled commands before developer PATH/Conda fallbacks.
- `src/research_agent/skills/registry.py` — discover built-in and installed Skills through runtime paths instead of `Path.cwd()`.
- `src/research_agent/web/index.html` — add first-run API configuration and About/tool-version sections.
- `src/research_agent/web/app.js` — retain the URL-fragment token, authenticate API calls, save/test configuration, and stop sending keys in plan requests.
- `src/research_agent/web/styles.css` — style first-run configuration, status messages, and About tool table.
- `tests/unit/test_launcher.py` — assert tokenized loopback launch and application task root.
- `tests/unit/test_conda_tool_resolver.py` — assert bundled-first resolution and packaged-mode isolation.
- `tests/integration/test_api.py` — adapt API calls to stored configuration and optional test token.

---

### Task 1: Authoritative package metadata and portable paths

**Files:**
- Create: `pyproject.toml`
- Create: `src/research_agent/runtime/__init__.py`
- Create: `src/research_agent/runtime/paths.py`
- Create: `tests/unit/test_runtime_paths.py`

**Interfaces:**
- Produces: `resource_root() -> Path`
- Produces: `AppPaths.for_runtime(home: Path | None = None, env: Mapping[str, str] | None = None) -> AppPaths`
- Produces fields: `support_dir`, `preferences_file`, `task_root`, `cache_dir`, `log_dir`, `installed_skill_root`

- [ ] **Step 1: Write failing path tests**

```python
from pathlib import Path

from research_agent.runtime.paths import AppPaths, resource_root


def test_app_paths_use_macos_user_directories(tmp_path):
    paths = AppPaths.for_runtime(home=tmp_path, env={})
    assert paths.support_dir == tmp_path / "Library/Application Support/PaleoRigor"
    assert paths.preferences_file == paths.support_dir / "preferences.json"
    assert paths.task_root == tmp_path / "Library/Caches/PaleoRigor/tasks"
    assert paths.log_dir == tmp_path / "Library/Logs/PaleoRigor"


def test_app_paths_allow_isolated_test_root(tmp_path):
    paths = AppPaths.for_runtime(home=tmp_path, env={"PALEORIGOR_DATA_ROOT": str(tmp_path / "isolated")})
    assert paths.support_dir == tmp_path / "isolated/support"
    assert paths.task_root == tmp_path / "isolated/cache/tasks"


def test_source_resource_root_contains_web_assets():
    assert (resource_root() / "web/index.html").is_file()
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_runtime_paths.py`

Expected: collection fails because `research_agent.runtime.paths` does not exist.

- [ ] **Step 3: Create package metadata and implement paths**

`pyproject.toml` must declare `local-research-agent==0.2.0`, Python `>=3.11,<3.14`, the dependencies recorded in `src/local_research_agent.egg-info/requires.txt`, a `research-agent = research_agent.launcher:main` script, `src` package discovery, and package data for `web/*`, `resources/*.json`, and `skill_packages/**/*`.

Implement `paths.py` with this public shape:

```python
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


def resource_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    return Path(frozen_root) / "research_agent" if frozen_root else Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppPaths:
    support_dir: Path
    preferences_file: Path
    task_root: Path
    cache_dir: Path
    log_dir: Path
    installed_skill_root: Path

    @classmethod
    def for_runtime(cls, home: Path | None = None, env: Mapping[str, str] | None = None) -> "AppPaths":
        source = os.environ if env is None else env
        home = Path.home() if home is None else Path(home)
        override = source.get("PALEORIGOR_DATA_ROOT")
        if override:
            root = Path(override).expanduser().resolve()
            support, cache, logs = root / "support", root / "cache", root / "logs"
        else:
            support = home / "Library/Application Support/PaleoRigor"
            cache = home / "Library/Caches/PaleoRigor"
            logs = home / "Library/Logs/PaleoRigor"
        return cls(support, support / "preferences.json", cache / "tasks", cache, logs, support / "skills")

    def ensure(self) -> None:
        for path in [self.support_dir, self.task_root, self.cache_dir, self.log_dir, self.installed_skill_root]:
            path.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run the focused tests and full pre-existing suite**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_runtime_paths.py tests/unit/test_config.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add pyproject.toml src/research_agent/runtime tests/unit/test_runtime_paths.py
git commit -m "feat: add portable macOS runtime paths"
```

---

### Task 2: Non-secret preferences and macOS Keychain storage

**Files:**
- Create: `src/research_agent/runtime/preferences.py`
- Create: `src/research_agent/runtime/secrets.py`
- Create: `tests/unit/test_preferences.py`
- Create: `tests/unit/test_secrets.py`

**Interfaces:**
- Produces: `JsonPreferences.load() -> dict[str, str]`
- Produces: `JsonPreferences.save(values: Mapping[str, str]) -> None`
- Produces: `SecretStore.get(name: str) -> str | None`, `set(name: str, value: str) -> None`, `delete(name: str) -> None`
- Produces: `MacOSKeychainSecretStore(service="org.paleorigor.app")`

- [ ] **Step 1: Write failing persistence and Keychain-command tests**

Test that preferences write through a sibling temporary file and contain only `api_base_url`, `model`, and `language`. Test a fake command runner receives exactly:

```text
/usr/bin/security find-generic-password -s org.paleorigor.app -a api_key -w
/usr/bin/security add-generic-password -U -s org.paleorigor.app -a api_key -w SECRET
/usr/bin/security delete-generic-password -s org.paleorigor.app -a api_key
```

Test that `repr(store)` and raised errors never include `SECRET`.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_preferences.py tests/unit/test_secrets.py`

Expected: imports fail because the modules do not exist.

- [ ] **Step 3: Implement atomic preferences and secret adapters**

Use `os.replace(temp_path, preferences_path)` for atomic preference writes. Define a `SecretStore` protocol, `MemorySecretStore` for tests, and `MacOSKeychainSecretStore` using an injected `runner` defaulting to `subprocess.run`. Treat Keychain exit code 44 as “not found”; convert other failures to `SecretStoreError("macOS Keychain operation failed")` without stderr or secret values.

- [ ] **Step 4: Run focused tests**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_preferences.py tests/unit/test_secrets.py`

Expected: all tests pass and no test output contains the sample secret.

- [ ] **Step 5: Commit Task 2**

```bash
git add src/research_agent/runtime/preferences.py src/research_agent/runtime/secrets.py tests/unit/test_preferences.py tests/unit/test_secrets.py
git commit -m "feat: store desktop credentials in macOS Keychain"
```

---

### Task 3: Redacted runtime configuration service

**Files:**
- Create: `src/research_agent/runtime/configuration.py`
- Create: `tests/unit/test_runtime_configuration.py`
- Modify: `src/research_agent/config.py`

**Interfaces:**
- Produces: `RuntimeApiConfig(base_url: str, model: str, api_key: str)`
- Produces: `RuntimeConfiguration.get() -> RuntimeApiConfig`
- Produces: `RuntimeConfiguration.update(base_url: str, model: str, api_key: str | None) -> dict[str, object]`
- Produces: `RuntimeConfiguration.delete_api_key() -> None`
- Produces redacted response: `{"base_url": ..., "model": ..., "api_key_present": bool}`

- [ ] **Step 1: Write failing configuration tests**

Cover defaults, preference reload, Keychain retrieval, key replacement, key deletion, whitespace stripping, rejection of non-HTTP(S) base URLs, rejection of empty models, and a recursive assertion that serialized responses do not contain the test key.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_runtime_configuration.py`

Expected: import failure for `research_agent.runtime.configuration`.

- [ ] **Step 3: Implement configuration service**

Use defaults `https://api.deepseek.com` and `deepseek-v4-flash`. Store only the URL, model, and language in JSON. Store the key under account `api_key` in Keychain. Keep `Settings.load()` compatible with environment-based tests, but add `Settings.from_runtime(config: RuntimeApiConfig, task_root: Path) -> Settings`.

- [ ] **Step 4: Run configuration tests**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_runtime_configuration.py tests/unit/test_config.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add src/research_agent/runtime/configuration.py src/research_agent/config.py tests/unit/test_runtime_configuration.py
git commit -m "feat: add redacted desktop API configuration"
```

---

### Task 4: Per-launch browser session protection

**Files:**
- Create: `src/research_agent/runtime/session.py`
- Create: `tests/unit/test_session_auth.py`
- Modify: `src/research_agent/main.py`

**Interfaces:**
- Produces: `generate_session_token() -> str` using `secrets.token_urlsafe(32)`
- Produces: `install_api_token_guard(app: FastAPI, expected_token: str | None) -> None`
- Header contract: `X-PaleoRigor-Token: <token>` for every `/api/` request when a token is configured

- [ ] **Step 1: Write failing middleware tests**

Create an app with `session_token="fixed-token"`. Assert `/` remains readable, `/api/health` returns 401 without a token, 401 with the wrong token, and 200 with `X-PaleoRigor-Token: fixed-token`. Assert error bodies and logs do not echo either token.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_session_auth.py`

Expected: `create_app()` rejects the new `session_token` argument.

- [ ] **Step 3: Implement middleware and health endpoint**

Change the app factory signature to:

```python
def create_app(
    task_root: Path | str | None = None,
    directory_chooser=None,
    runtime_configuration: RuntimeConfiguration | None = None,
    session_token: str | None = None,
) -> FastAPI:
```

Use `hmac.compare_digest` inside middleware. Return `{"detail": {"error": "invalid_session"}}` with HTTP 401. Add `GET /api/health` returning `{"status": "ok", "version": "0.2.0"}`.

- [ ] **Step 4: Run middleware and existing API tests**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_session_auth.py tests/integration/test_api.py`

Expected: all tests pass; existing tests remain unauthenticated because their app factory passes `session_token=None`.

- [ ] **Step 5: Commit Task 4**

```bash
git add src/research_agent/runtime/session.py src/research_agent/main.py tests/unit/test_session_auth.py tests/integration/test_api.py
git commit -m "feat: protect local API with launch token"
```

---

### Task 5: Bundled-first tool and Skill resource discovery

**Files:**
- Create: `src/research_agent/resources/tool_manifest.json`
- Modify: `src/research_agent/skills/conda_tools.py`
- Modify: `src/research_agent/skills/registry.py`
- Modify: `tests/unit/test_conda_tool_resolver.py`
- Modify: `tests/unit/test_skill_registry.py`

**Interfaces:**
- Produces: `bundled_tool_root(env: Mapping[str, str] | None = None) -> Path | None`
- Extends: `resolve_tool(executable_candidates, tool_envs=None, bundle_root=None, packaged=False) -> ToolCommand | None`
- Resolution order in developer mode: bundle, PATH, configured Conda
- Resolution order in packaged mode: bundle only

- [ ] **Step 1: Write failing bundled-resolution tests**

Create `tmp_path/tools/bin/fastqc`, make it executable, and assert resolution returns:

```python
ToolCommand(tool="fastqc", command=[str(executable)], source="bundle")
```

Assert it wins over a mocked `/usr/local/bin/fastqc`. Assert `packaged=True` returns `None` rather than falling back to PATH or Conda when the bundled file is missing. Assert installed Skills use `AppPaths.installed_skill_root` rather than `Path.cwd()`.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_conda_tool_resolver.py tests/unit/test_skill_registry.py`

Expected: tests fail because bundled arguments and runtime Skill paths are absent.

- [ ] **Step 3: Implement manifest and bundled-first resolution**

The manifest contains seven entries with fields `id`, `version`, `command`, and `license_file`. Commands are `bin/fastqc`, `bin/multiqc`, `bin/seqkit`, `bin/seqtk`, `bin/samtools`, `bin/bwa`, and `bin/bowtie2`. Load the bundle root from explicit arguments first and `PALEORIGOR_TOOL_ROOT` second. Reject any manifest command that escapes the tool root after resolution.

Change `builtin_skill_root()` to `resource_root() / "skill_packages/builtin"` and `installed_skill_root()` to `AppPaths.for_runtime().installed_skill_root`.

- [ ] **Step 4: Run resolver, registry, and Skill readiness tests**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_conda_tool_resolver.py tests/unit/test_skill_registry.py tests/unit/test_skill_readiness_contracts.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 5**

```bash
git add src/research_agent/resources/tool_manifest.json src/research_agent/skills/conda_tools.py src/research_agent/skills/registry.py tests/unit/test_conda_tool_resolver.py tests/unit/test_skill_registry.py
git commit -m "feat: resolve packaged bioinformatics tools first"
```

---

### Task 6: First-run configuration, About API, and stored-key planning

**Files:**
- Create: `tests/integration/test_runtime_config_api.py`
- Modify: `src/research_agent/main.py`
- Modify: `tests/integration/test_api.py`

**Interfaces:**
- Adds: `GET /api/config`
- Adds: `PUT /api/config` with `{"base_url": str, "model": str, "api_key": str | null}`
- Adds: `DELETE /api/config/key`
- Adds: `POST /api/config/test`
- Adds: `GET /api/about`
- Changes: `PlanRequest` to contain only `instruction: str`

- [ ] **Step 1: Write failing API tests**

Use `MemorySecretStore` and temporary preferences. Verify API responses never include a key. Inject an `httpx.MockTransport`-backed planner client factory so the connection test and planning test do not use the internet. Verify a plan request succeeds with `{"instruction": "..."}` and the planner receives the stored base URL, model, and API key.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/integration/test_runtime_config_api.py`

Expected: configuration endpoints return 404 and stored-key planning is unsupported.

- [ ] **Step 3: Implement configuration endpoints and planner injection**

Add Pydantic request models with `extra="forbid"`. `POST /api/config/test` sends a minimal JSON-only request to the configured model and returns only `{"status": "ok", "model": configured_model}`. Map authentication errors to `invalid_api_credentials`, transport errors to `api_unreachable`, and malformed responses to `invalid_api_response`; do not return raw response bodies or authorization details.

Read `tool_manifest.json` for `GET /api/about`, returning application version, GitHub URL `https://github.com/Verture-Liu/2026summerproject`, and the seven tool IDs and pinned versions.

- [ ] **Step 4: Run API tests**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/integration/test_runtime_config_api.py tests/integration/test_api.py tests/unit/test_planner.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 6**

```bash
git add src/research_agent/main.py tests/integration/test_runtime_config_api.py tests/integration/test_api.py
git commit -m "feat: add secure first-run API configuration"
```

---

### Task 7: Browser authentication and first-run interface

**Files:**
- Modify: `src/research_agent/web/index.html`
- Modify: `src/research_agent/web/app.js`
- Modify: `src/research_agent/web/styles.css`
- Modify: `tests/unit/test_english_ui.py`
- Create: `tests/unit/test_desktop_ui_contract.py`

**Interfaces:**
- URL fragment contract: `#token=<percent-encoded-token>`
- Browser request header: `X-PaleoRigor-Token`
- First-run state: configuration panel remains blocking until `api_key_present` is true and the connection test succeeds

- [ ] **Step 1: Write failing static UI contract tests**

Read the three web files as text. Assert the HTML contains IDs `api-config-panel`, `api-base-url`, `api-model`, `api-key`, `save-api-config`, `test-api-config`, `about-tools`, and `config-status`. Assert JavaScript reads `window.location.hash`, immediately calls `history.replaceState` to remove the fragment, stores the token only in module memory, sets `X-PaleoRigor-Token`, and sends plan bodies without an `api` or `api_key` field.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_desktop_ui_contract.py tests/unit/test_english_ui.py`

Expected: missing-element and missing-token assertions fail.

- [ ] **Step 3: Implement the first-run and About interface**

Add a compact configuration card above task creation. Use `type="password"`, `autocomplete="off"`, and never repopulate the key input from the backend. Add English and Chinese strings for configuration saved, connection passed, invalid credentials, unreachable API, and missing configuration. Disable task planning until configuration is ready. Render the seven-tool version table from `/api/about`.

- [ ] **Step 4: Run UI contract tests**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_desktop_ui_contract.py tests/unit/test_english_ui.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 7**

```bash
git add src/research_agent/web tests/unit/test_desktop_ui_contract.py tests/unit/test_english_ui.py
git commit -m "feat: add secure desktop first-run interface"
```

#### Final regression report (2026-08-23)

- Superseding a pending Save or Test action with another configuration action now clears the prior button's loading and disabled state before the newer action becomes busy.
- Save, Test, and Delete share one generation-aware busy-state manager. Only the current action can restore the complete configuration control group; stale responses still cannot alter configuration readiness, status, or data.
- Verification: `env PYTHONPATH=src /Users/tianaoliu/Documents/vscode/2026summerproject/.venv/bin/pytest -q tests/integration/test_api.py tests/integration/test_runtime_config_api.py tests/unit/test_config.py tests/unit/test_desktop_ui_contract.py tests/unit/test_english_ui.py tests/unit/test_preferences.py tests/unit/test_runtime_configuration.py tests/unit/test_secrets.py tests/unit/test_session_auth.py` — 59 passed (one third-party TestClient deprecation warning).

---

### Task 8: Tokenized launcher and portable backend smoke test

**Files:**
- Modify: `src/research_agent/launcher.py`
- Modify: `tests/unit/test_launcher.py`
- Create: `tests/integration/test_desktop_runtime_smoke.py`

**Interfaces:**
- Adds: `build_browser_url(host: str, port: int, token: str) -> str`
- Adds: `build_runtime() -> tuple[AppPaths, RuntimeConfiguration, str]`
- Launcher URL shape: `http://127.0.0.1:<port>/#token=<encoded-token>`

- [ ] **Step 1: Write failing launcher tests**

Mock `webbrowser.open` and `uvicorn.run`. Assert the URL uses a fragment, the token is not passed in query parameters, the app is created with the same token, and the task root comes from `AppPaths`. Assert the launcher creates support/cache/log directories before starting Uvicorn.

- [ ] **Step 2: Run tests and verify RED**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_launcher.py tests/integration/test_desktop_runtime_smoke.py`

Expected: missing URL/runtime helpers cause failure.

- [ ] **Step 3: Refactor launcher to build the app object directly**

Replace the string `"research_agent.main:app"` with an injected app object returned by `create_app(...)`. Generate the token once per launch. Build the browser URL with `urllib.parse.quote(token, safe="")`. Do not print the token or URL. Set `log_config=None` only in packaged mode; preserve normal developer logs otherwise.

- [ ] **Step 4: Run launcher and full test suite**

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_launcher.py tests/integration/test_desktop_runtime_smoke.py`

Run: `env PYTHONPATH=src .venv/bin/pytest -q tests`

Expected: all tests pass with no warnings containing an API key or session token.

- [ ] **Step 5: Run a manual developer-mode smoke test**

Run: `PALEORIGOR_DATA_ROOT=/tmp/paleorigor-phase1 env PYTHONPATH=src .venv/bin/research-agent`

Expected: the browser opens, first-run configuration is shown, `/api/` calls succeed only from the tokenized page, the About page lists all seven pinned tools, and quitting the terminal process stops the backend.

- [ ] **Step 6: Commit Task 8**

```bash
git add src/research_agent/launcher.py tests/unit/test_launcher.py tests/integration/test_desktop_runtime_smoke.py
git commit -m "feat: launch portable tokenized desktop runtime"
```

---

## Phase 1 Completion Gate

- [ ] Run `env PYTHONPATH=src .venv/bin/pytest -q tests` and record the exact pass count.
- [ ] Run `env PYTHONPATH=src .venv/bin/python -m build` and confirm both wheel and source distribution are created.
- [ ] Install the wheel into a clean temporary virtual environment outside the repository.
- [ ] Run the installed `research-agent --no-browser`, call authenticated `/api/health`, `/api/config`, and `/api/about`, and confirm source resources are present.
- [ ] Run a secret scan over source, tests, build metadata, and generated logs; confirm no API key or session token was persisted.
- [ ] Record Python, macOS, and dependency versions in `packaging/macos/phase1-verification.json` during execution.
- [ ] Do not begin Phase 2 until every Phase 1 gate is green.

## Subsequent Approved Plans

After Phase 1 passes, write and execute:

1. `2026-08-23-paleorigor-macos-phase2-app-bundle.md` for the PyInstaller backend, native Swift launcher, FastQC Java runtime, MultiQC packaging, native tool binaries and transitive libraries, tool-integrity manifest, `.app` assembly, and unsigned development DMG.
2. `2026-08-23-paleorigor-macos-phase3-release.md` for Developer ID signing, hardened runtime, entitlements, notarization, stapling, licenses, GitHub release artifacts, and clean Apple Silicon Mac acceptance testing.

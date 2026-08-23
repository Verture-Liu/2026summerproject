# Task 8 report

Status: implemented and verified. Phase 2 was not started.

## Runtime change

`research_agent.launcher` now composes `AppPaths`, `RuntimeConfiguration` with `MacOSKeychainSecretStore`, and one session token for each launch. It creates the runtime directories before starting, passes the resulting `create_app(...)` object directly to Uvicorn on `127.0.0.1`, and opens only a fragment-token URL. The token is percent-encoded in the fragment, never added to a query string, and is neither printed nor logged. The existing `--no-browser` option remains supported. Packaged launches disable Uvicorn logging; developer launches retain it.

## TDD evidence

- RED: the focused test run before implementation reported 5 failures and 2 passes. Four failures were the absent Task 8 URL/runtime helpers; the existing free-port test could not bind in the sandbox.
- GREEN: `env PYTHONPATH=src ../../.venv/bin/pytest -q tests/unit/test_launcher.py tests/integration/test_desktop_runtime_smoke.py` reported 7 passed, with one existing Starlette deprecation warning.

## Verification

- Full suite: `env PYTHONPATH=src ../../.venv/bin/pytest -q tests` — 250 passed, 1 existing Starlette deprecation warning.
- Build: `env PYTHONPATH=src ../../.venv/bin/python -m build` produced `local_research_agent-0.2.0-py3-none-any.whl` and `local_research_agent-0.2.0.tar.gz`.
- Final wheel SHA-256: `5282627c0aad8786f195a1aeb201ece8e997bdf38f249132491824d39575df4e`.
- Final sdist SHA-256: `0143faed2ddd4273e4386aeebad42b43d97437d863c8783da3a13adfc994cffa`.
- Clean install: the final wheel installed into a newly created temporary Python 3.13.9 virtual environment.
- Installed smoke: installed `research-agent --no-browser` served authenticated `/api/health`, `/api/config`, and `/api/about`; unauthenticated health returned 401; seven tool-manifest entries and the installed resource manifest were present. A temporary subprocess-only Keychain/token substitute ensured no real macOS Keychain access.
- Secret scan: source, tests, build metadata, distribution artifacts, and generated smoke logs/responses had no persisted API-key, Authorization-header, or session-token-value findings. Fragment construction and explicit non-secret test fixtures are expected source text.

## Environment and LFS

The gate ran on macOS 26.5.2 (25F84), arm64. The test environment used Python 3.13.9; the installed wheel reports version 0.2.0. Git LFS is unavailable and was not used: `enabled=false`, `tracked_files=0`, `upload_performed=false`.

Detailed machine-readable evidence is in `packaging/macos/phase1-verification.json`.

## Gate concerns

- This worktree has no local `.venv`; the repository virtual environment at `../../.venv` was used.
- The full suite has one pre-existing Starlette TestClient deprecation warning.
- The source-distribution build has a non-fatal missing README warning.
- GUI browser interaction was intentionally replaced by the installed no-browser authenticated endpoint/resource smoke because GUI automation is unsafe in this environment.

## Final-review fix wave (2026-08-23)

Status: all Critical/Important final-review findings were fixed and verified in one Phase 1 wave. Phase 2 was not started.

### Security and runtime corrections

- Provider-derived workflow content is scanned recursively for the exact configured nonempty API key before parsing/repair return, API return, draft/final workflow writes, validation propagation, execution, or record generation. String keys and nested string values are covered; empty keys are ignored. Contamination raises only stable generic errors and never includes the provider body or key.
- Packaged mode is inferred centrally from `sys.frozen` or `sys._MEIPASS` unless an explicit override is supplied. Resolver calls made by real Skills are bundle-only in packaged mode and retain PATH/Conda behavior in developer mode.
- Backend PUT/DELETE configuration mutations share one async lock. Reads and connection tests take a consistent snapshot without mutating configuration. `RuntimeConfiguration.update()` stages a replacement secret first and restores the old key and preferences if preference commit fails; secret-store set failure leaves preferences untouched.
- The browser disables configuration inputs and every configuration action while Save/Delete is pending. Test remains a read-only backend operation and can be superseded safely without changing backend state.
- API/session tokens remain module-memory-only and are not stored in local/session storage or cookies. Refresh therefore intentionally loses the token; a 401 `invalid_session` disables controls and displays a clear quit-and-relaunch message. This relaunch cost is a deliberate security tradeoff against persisting a bearer token in browser-managed storage.
- Wheel and sdist metadata now exclude `.pyc`, `.pyo`, and `__pycache__` content. Simulated `_MEIPASS` resource discovery is covered directly.

### Adversarial TDD evidence

- RED reproduced each finding: provider echo returned 200, contaminated execution reached validation, Save/Delete restored a deleted key, failed secret storage left new preferences, frozen Skill calls could reach developer resolution, refresh lacked a relaunch state, and package metadata lacked bytecode exclusions.
- GREEN focused suite: 65 passed with one existing Starlette deprecation warning.
- Full suite: `env PYTHONPATH=src ../../.venv/bin/pytest -q tests` — 263 passed with one existing Starlette deprecation warning.

### Build, install, smoke, and scans

- Clean build: removed prior `build/`, `dist/`, and generated egg-info state, then rebuilt `local_research_agent-0.2.0-py3-none-any.whl` and `local_research_agent-0.2.0.tar.gz` with `python -m build`.
- Wheel SHA-256: `7c95dc11ff0339dbad5c9a51160c9672e1bf2701c43049a2c0e7030b8b4eef28` (107K).
- Sdist SHA-256: `573f71fc796a6baffa195aec1e54d8c738aac9400d05d650720b242b5e4a2a18` (73K).
- Extracted archive scan: zero `.pyc`/`.pyo` files, zero `__pycache__` directories, zero developer-path findings, and zero known test-secret findings.
- Clean install: installed the rebuilt wheel and dependencies into `/tmp/paleorigor-phase1-final-smoke/venv`.
- Installed authenticated smoke: `/api/health`, `/api/config`, and `/api/about` returned 200; unauthenticated health returned 401 `invalid_session`; all seven tool entries and packaged web/manifest resources were present; shutdown completed cleanly; the real Keychain was not touched.
- Installed adversarial provider-echo smoke: returned 502 `planning_failed`; no workflow draft, workflow record, manifest, report, result directory, response echo, or canary-bearing artifact was created. The only generated file was non-secret `preferences.json`.
- Session-token persistence scan: zero findings in installed application data or environment. The known token existed only in the explicit temporary smoke harness source.

### Remaining verification concerns

- One Starlette `TestClient` deprecation warning remains.
- The sdist build retains the non-fatal missing README warning.
- Node.js is unavailable, so there was no `node --check`; browser JavaScript is covered by 17 UI contracts plus the installed authenticated backend smoke.
- The installed smoke used an in-memory Keychain substitute to avoid changing the user's real credentials; Keychain command behavior remains covered by unit tests.

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

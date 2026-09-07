# Empty API Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make fresh PaleoRigor installations provider-neutral while preserving user-saved API settings and never redisplaying API keys.

**Architecture:** Runtime configuration will use empty strings as its only fresh-install and invalid-legacy fallback values. The browser will render neutral placeholders, restore only saved URL/model values, and validate all three required values before save/test actions. Existing preference and secret-store boundaries remain unchanged.

**Tech Stack:** Python 3, FastAPI, vanilla JavaScript/HTML, pytest

## Global Constraints

- Fresh API URL, model name, and API key values are empty.
- Saved URL and model values persist; API keys never appear in browser inputs or API responses.
- English and Chinese messages identify each missing field.
- No planner, API-protocol, or packaging-content changes.

---

### Task 1: Provider-neutral runtime defaults

**Files:**
- Modify: `tests/unit/test_runtime_configuration.py`
- Modify: `tests/integration/test_runtime_config_api.py`
- Modify: `src/research_agent/runtime/configuration.py`

**Interfaces:**
- `RuntimeConfiguration.get() -> RuntimeApiConfig` returns stored values or empty strings.
- `RuntimeConfiguration.update(base_url, model, api_key)` continues preserving an existing key when `api_key` is `None`.

- [x] Change fresh-profile and unsafe-legacy fallback expectations to empty strings.
- [x] Run focused tests and verify they fail on the DeepSeek defaults.
- [x] Replace DeepSeek constants with empty defaults and avoid URL normalization for an absent URL.
- [x] Run focused tests and verify they pass.

### Task 2: Neutral browser form and exact missing-field feedback

**Files:**
- Modify: `tests/unit/test_desktop_ui_contract.py`
- Modify: `src/research_agent/web/index.html`
- Modify: `src/research_agent/web/app.js`

**Interfaces:**
- `missingConfigurationFields({includeInputKey}) -> string[]` returns translated field labels absent from the form/stored-key state.
- Save and test handlers stop before network access and display `configurationFieldsMissing` when required values are absent.

- [x] Add contract assertions for neutral placeholders, no embedded DeepSeek value, and exact missing-field validation.
- [x] Run the UI contract tests and verify the new assertions fail.
- [x] Add English/Chinese missing-field copy and minimal client-side validation while keeping the key input blank after every configuration response.
- [x] Run UI contract tests and verify they pass.

### Task 3: Regression verification

**Files:**
- Verify only; no planned production changes.

- [x] Run runtime configuration, API integration, UI contract, and packaging contract tests.
- [x] Run `git diff --check` and inspect the focused diff for secret values and unintended files.
- [x] Commit only the implementation, tests, design, and plan files.

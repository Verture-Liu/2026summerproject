import re
from pathlib import Path


WEB_DIR = Path("src/research_agent/web")


def read_web_files():
    return {
        "html": (WEB_DIR / "index.html").read_text(encoding="utf-8"),
        "javascript": (WEB_DIR / "app.js").read_text(encoding="utf-8"),
        "styles": (WEB_DIR / "styles.css").read_text(encoding="utf-8"),
    }


def test_desktop_configuration_and_about_elements_are_present():
    files = read_web_files()

    for element_id in (
        "api-config-panel",
        "api-base-url",
        "api-model",
        "api-key",
        "save-api-config",
        "test-api-config",
        "about-tools",
        "config-status",
    ):
        assert f'id="{element_id}"' in files["html"]

    assert 'id="api-key" type="password" autocomplete="off"' in files["html"]
    assert "#api-config-panel" in files["styles"]


def test_desktop_token_is_taken_from_fragment_then_removed_from_url():
    javascript = read_web_files()["javascript"]

    assert "window.location.hash" in javascript
    assert "#token=" in javascript
    assert "decodeURIComponent" in javascript
    assert "history.replaceState" in javascript
    assert "let sessionToken" in javascript
    assert "localStorage" not in javascript
    assert "sessionStorage" not in javascript
    assert "document.cookie" not in javascript


def test_every_api_fetch_uses_the_fragment_token_header():
    javascript = read_web_files()["javascript"]

    assert "const apiFetch" in javascript
    assert '"X-PaleoRigor-Token": sessionToken' in javascript
    assert 'headers: {...options.headers, "X-PaleoRigor-Token": sessionToken}' in javascript
    assert not re.search(r'fetch\(\s*[`\"]/?api/', javascript)
    assert len(re.findall(r'apiFetch\(', javascript)) >= 8
    assert 'href = `/api/' not in javascript
    assert 'apiFetch(`/api/tasks/${taskId}/report`)' in javascript


def test_plan_request_uses_only_stored_api_configuration():
    javascript = read_web_files()["javascript"]

    plan_handler = javascript.split('$("plan").onclick = async () => {', 1)[1].split(
        '$("selectOutput").onclick', 1
    )[0]
    assert 'body: JSON.stringify({instruction: $("instruction").value})' in plan_handler
    assert "api_key" not in plan_handler
    assert "api:" not in plan_handler


def test_first_run_stays_blocking_until_key_and_connection_test_pass():
    javascript = read_web_files()["javascript"]

    assert "let configurationReady = false" in javascript
    assert "api_key_present" in javascript
    assert 'apiFetch("/api/config/test"' in javascript
    assert '$("plan").disabled = !(configurationReady && hasFiles);' in javascript
    assert '$("api-key").value = ""' in javascript


def test_desktop_can_delete_a_saved_key_without_exposing_it_or_enabling_planning():
    files = read_web_files()
    html = files["html"]
    javascript = files["javascript"]

    assert 'id="delete-api-key"' in html
    assert 'data-i18n="deleteApiKey"' in html
    assert 'aria-describedby="config-status"' in html
    assert "Delete API Key" in javascript
    assert "删除 API 密钥" in javascript
    assert 'apiFetch("/api/config/key", {method: "DELETE"})' in javascript
    assert '$("api-key").value = ""' in javascript
    assert "apiKeyPresent = false" in javascript
    assert "configurationReady = false" in javascript
    assert "apiKeyDeleted" in javascript
    assert "apiKeyDeleteFailed" in javascript


def test_initial_configuration_response_cannot_overwrite_newer_configuration_state():
    javascript = read_web_files()["javascript"]

    assert "let configurationGeneration = 0" in javascript
    assert "const beginConfigurationAction = () => ++configurationGeneration" in javascript
    assert "const requestGeneration = configurationGeneration" in javascript
    assert "if (!isCurrentConfigurationAction(requestGeneration)) return;" in javascript
    assert "beginConfigurationAction();" in javascript


def test_configuration_actions_cannot_restore_stale_ui_after_a_newer_action():
    javascript = read_web_files()["javascript"]

    assert "const isCurrentConfigurationAction = (generation) => generation === configurationGeneration" in javascript

    initial_load = javascript.split("const loadInitialConfiguration = async () => {", 1)[1].split(
        "const initializeDesktopInterface", 1
    )[0]
    assert "const requestGeneration = configurationGeneration;" in initial_load
    assert initial_load.index("const requestGeneration") < initial_load.index("await apiFetch")
    assert initial_load.count("if (!isCurrentConfigurationAction(requestGeneration)) return;") >= 3
    initial_fetch = initial_load.index("await apiFetch")
    initial_json = initial_load.index("await safeResponseJson")
    initial_first_guard = initial_load.index("if (!isCurrentConfigurationAction(requestGeneration)) return;", initial_fetch)
    initial_second_guard = initial_load.index("if (!isCurrentConfigurationAction(requestGeneration)) return;", initial_first_guard + 1)
    assert initial_fetch < initial_first_guard < initial_json < initial_second_guard

    for action, next_action in (
        ('$("save-api-config").onclick = async () => {', '$("test-api-config").onclick'),
        ('$("test-api-config").onclick = async () => {', '$("delete-api-key").onclick'),
        ('$("delete-api-key").onclick = async () => {', '$("upload").onclick'),
    ):
        handler = javascript.split(action, 1)[1].split(next_action, 1)[0]
        assert "const requestGeneration = beginConfigurationAction();" in handler
        assert handler.index("const requestGeneration") < handler.index("await apiFetch")
        assert "await apiFetch" in handler
        assert "await safeResponseJson" in handler
        assert handler.count("if (!isCurrentConfigurationAction(requestGeneration)) return;") >= 4
        assert "catch (_error) {\n    if (!isCurrentConfigurationAction(requestGeneration)) return;" in handler
        assert "finally {\n    if (!isCurrentConfigurationAction(requestGeneration)) return;" in handler
        fetch_index = handler.index("await apiFetch")
        json_index = handler.index("await safeResponseJson")
        first_guard = handler.index("if (!isCurrentConfigurationAction(requestGeneration)) return;", fetch_index)
        second_guard = handler.index("if (!isCurrentConfigurationAction(requestGeneration)) return;", first_guard + 1)
        finally_guard = handler.index("finally {\n    if (!isCurrentConfigurationAction(requestGeneration)) return;")
        assert fetch_index < first_guard < json_index < second_guard
        assert finally_guard < handler.index("setButtonLoading", finally_guard)

    test_handler = javascript.split('$("test-api-config").onclick = async () => {', 1)[1].split(
        '$("delete-api-key").onclick', 1
    )[0]
    response_guard = test_handler.index("if (!isCurrentConfigurationAction(requestGeneration)) return;")
    json_guard = test_handler.index("if (!isCurrentConfigurationAction(requestGeneration)) return;", response_guard + 1)
    assert json_guard < test_handler.index("configurationReady = true")


def test_about_renders_the_packaged_tool_versions():
    javascript = read_web_files()["javascript"]

    assert 'apiFetch("/api/about")' in javascript
    assert '$("about-tools")' in javascript
    assert "data.tools" in javascript

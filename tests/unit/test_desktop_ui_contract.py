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
    assert "if (requestGeneration !== configurationGeneration) return;" in javascript
    assert "beginConfigurationAction();" in javascript


def test_about_renders_the_packaged_tool_versions():
    javascript = read_web_files()["javascript"]

    assert 'apiFetch("/api/about")' in javascript
    assert '$("about-tools")' in javascript
    assert "data.tools" in javascript

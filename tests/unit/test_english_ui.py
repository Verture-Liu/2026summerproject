import re
from pathlib import Path

from research_agent.execution.exporter import RECORDS_DIR


CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")


def test_web_html_defaults_to_english_without_inline_chinese():
    web_dir = Path("src/research_agent/web")
    html = (web_dir / "index.html").read_text(encoding="utf-8")
    html_without_language_button = html.replace("中文", "")
    assert CJK_PATTERN.search(html_without_language_button) is None
    assert '<html lang="en">' in html


def test_web_ui_has_simple_language_switcher():
    web_dir = Path("src/research_agent/web")
    html = (web_dir / "index.html").read_text(encoding="utf-8")
    javascript = (web_dir / "app.js").read_text(encoding="utf-8")
    assert 'id="languageToggle"' in html
    assert 'data-i18n="heroTitle"' in html
    assert "const translations" in javascript
    assert "setLanguage" in javascript
    assert "中文" in html
    assert "English" in html


def test_records_directory_name_is_english():
    assert RECORDS_DIR == "ResearchAgent Records"


def test_web_ui_reuses_one_run_report_link():
    web_dir = Path("src/research_agent/web")
    html = (web_dir / "index.html").read_text(encoding="utf-8")
    javascript = (web_dir / "app.js").read_text(encoding="utf-8")
    assert html.count('id="reportLink"') == 1
    assert 'document.createElement("a")' not in javascript
    assert '$("status").after(link)' not in javascript


def test_web_ui_has_visible_progress_steps():
    html = Path("src/research_agent/web/index.html").read_text(encoding="utf-8")
    assert 'id="progressSteps"' in html
    for label in (
        "Model API",
        "Upload files",
        "Plan workflow",
        "Choose output",
        "Run locally",
    ):
        assert label in html


def test_web_ui_shows_loading_and_running_feedback():
    javascript = Path("src/research_agent/web/app.js").read_text(encoding="utf-8")
    for message in (
        "Uploading files...",
        "Planning workflow...",
        "Waiting for folder selection...",
        "Running workflow locally...",
        "Local execution is running. Some tools may take several minutes.",
    ):
        assert message in javascript
    assert "setStepState" in javascript
    assert "setButtonLoading" in javascript


def test_web_ui_has_bilingual_first_run_configuration_feedback():
    javascript = Path("src/research_agent/web/app.js").read_text(encoding="utf-8")

    for message in (
        "Configuration saved.",
        "Connection passed.",
        "Invalid API credentials.",
        "The API could not be reached.",
        "Complete and test the API configuration before planning a workflow.",
        "配置已保存。",
        "连接测试通过。",
        "API 凭据无效。",
        "无法连接 API。",
        "请先完成并测试 API 配置，再生成 workflow。",
    ):
        assert message in javascript

from pathlib import Path
from html.parser import HTMLParser
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "docs/index.html"
CSS = ROOT / "docs/assets/site.css"
JS = ROOT / "docs/assets/site.js"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag == "a" and "href" in values:
            self.hrefs.append(values["href"])


class PublicSiteTests(unittest.TestCase):
    def test_required_files_exist(self):
        for path in (HTML, CSS, JS):
            self.assertTrue(path.is_file(), path)

    def test_page_identifies_public_and_local_modes(self):
        text = HTML.read_text(encoding="utf-8")
        self.assertIn("Public website", text)
        self.assertIn("Local application", text)
        self.assertIn("View on GitHub", text)
        self.assertIn("Run locally", text)

    def test_verified_numbers_are_present(self):
        text = HTML.read_text(encoding="utf-8")
        for value in (
            "12/12",
            "1/4",
            "six public sequencing records",
            "114",
            "5,696",
        ):
            self.assertIn(value, text)

    def test_repository_links_are_direct(self):
        text = HTML.read_text(encoding="utf-8")
        url = "https://github.com/Verture-Liu/2026summerproject"
        self.assertGreaterEqual(text.count(url), 2)

    def test_static_page_has_no_data_or_key_inputs(self):
        text = HTML.read_text(encoding="utf-8").lower()
        self.assertNotRegex(text, r'<input[^>]+type=["\']file["\']')
        self.assertNotRegex(text, r'<input[^>]+type=["\']password["\']')
        self.assertNotIn("/api/tasks", text)

    def test_assets_use_project_relative_paths(self):
        text = HTML.read_text(encoding="utf-8")
        self.assertIn('href="assets/site.css"', text)
        self.assertIn('src="assets/site.js"', text)
        self.assertNotIn('href="/assets/', text)
        self.assertNotIn('src="/assets/', text)

    def test_styles_include_responsive_and_accessibility_rules(self):
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("@media (max-width:", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_javascript_only_enhances_navigation_and_copying(self):
        script = JS.read_text(encoding="utf-8")
        self.assertIn("navigator.clipboard", script)
        self.assertIn("menu-toggle", script)
        self.assertNotIn("fetch(", script)

    def test_page_anchors_and_internal_files_resolve(self):
        parser = LinkParser()
        parser.feed(HTML.read_text(encoding="utf-8"))
        for href in parser.hrefs:
            if href.startswith("#"):
                self.assertIn(href[1:], parser.ids, href)
            elif not re.match(r"^[a-z]+://", href):
                self.assertTrue((HTML.parent / href).is_file(), href)


if __name__ == "__main__":
    unittest.main()

# PaleoRigor Public Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an English-only, static GitHub Pages website that explains PaleoRigor to paleobiologists, presents verified evidence, and directs users to the GitHub repository for full local execution.

**Architecture:** The public site lives entirely under `docs/` and uses semantic HTML, a focused stylesheet, and minimal JavaScript. It does not call the Python API or execute Skills. A small Python unittest suite validates page content, relative asset paths, quantitative claims, and the separation between public exploration and local execution.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Python `unittest`, GitHub Pages.

## Global Constraints

- English only.
- Static hosting with no Python, Node.js, database, API key input, upload form, or rented server.
- Repository URL: `https://github.com/Verture-Liu/2026summerproject`.
- Real analysis remains in the existing local Python application.
- Existing files under `src/research_agent/web/` are not modified.
- Quantitative claims must remain: 12/12 supported runs, 1/4 boundary requests, six source records, 114 duplicates removed, and 5,696 retained records.
- The site must not claim ancient-molecule authentication, contamination-source identification, autonomous interpretation, or cloud execution.

---

### Task 1: Static-site contract tests

**Files:**
- Create: `tests/site/__init__.py`
- Create: `tests/site/test_public_site.py`

**Interfaces:**
- Consumes: planned files `docs/index.html`, `docs/assets/site.css`, and `docs/assets/site.js`.
- Produces: a repeatable acceptance contract for required copy, URLs, assets, and prohibited controls.

- [ ] **Step 1: Write the failing site contract tests**

Create tests that:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "docs/index.html"
CSS = ROOT / "docs/assets/site.css"
JS = ROOT / "docs/assets/site.js"


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
        for value in ("12/12", "1/4", "six public sequencing records", "114", "5,696"):
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
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `.venv/bin/python -m unittest tests/site/test_public_site.py -v`

Expected: failures because the new page and assets do not yet exist.

- [ ] **Step 3: Commit the test contract**

```bash
git add tests/site
git commit -m "test: define PaleoRigor public site contract"
```

---

### Task 2: Semantic public landing page

**Files:**
- Create: `docs/index.html`
- Create: `docs/.nojekyll`
- Test: `tests/site/test_public_site.py`

**Interfaces:**
- Consumes: repository URL and verified manuscript claims from the design specification.
- Produces: semantic sections with IDs `overview`, `workflow`, `capabilities`, `evidence`, `review`, and `run-local`.

- [ ] **Step 1: Implement the minimal semantic HTML**

Create a complete HTML document containing:

```html
<header class="site-header">...</header>
<main>
  <section id="overview">...</section>
  <section id="workflow">...</section>
  <section id="capabilities">...</section>
  <section id="evidence">...</section>
  <section id="review">...</section>
  <section id="run-local">...</section>
</main>
<footer>...</footer>
```

Required content:

- PaleoRigor name and a paleobiology-facing value statement.
- GitHub and local-run actions.
- Four practical risks before biological interpretation.
- CSS-native workflow stages: question, plan, review, local Skills, auditable outputs.
- Capability cards grouped by scientific purpose.
- Evidence cards with the locked quantitative values.
- Three expert checkpoints.
- Copyable commands:

```bash
git clone https://github.com/Verture-Liu/2026summerproject.git
cd 2026summerproject
python -m venv .venv
source .venv/bin/activate
pip install -e .
research-agent
```

- Explicit scope language that source verification is not ancient-DNA authentication.
- Relative links to `assets/site.css` and `assets/site.js`.

- [ ] **Step 2: Run the contract tests**

Run: `.venv/bin/python -m unittest tests/site/test_public_site.py -v`

Expected: file/content tests pass; visual behavior is not yet assessed.

- [ ] **Step 3: Commit the semantic page**

```bash
git add docs/index.html docs/.nojekyll
git commit -m "feat: add PaleoRigor public landing page"
```

---

### Task 3: Scientific visual system and responsive layout

**Files:**
- Create: `docs/assets/site.css`
- Test: `tests/site/test_public_site.py`

**Interfaces:**
- Consumes: semantic classes and section IDs from `docs/index.html`.
- Produces: a responsive, accessible layout without external fonts or image dependencies.

- [ ] **Step 1: Add a failing responsive-style test**

Add:

```python
def test_styles_include_responsive_and_accessibility_rules(self):
    css = CSS.read_text(encoding="utf-8")
    self.assertIn("@media (max-width:", css)
    self.assertIn(":focus-visible", css)
    self.assertIn("prefers-reduced-motion", css)
```

- [ ] **Step 2: Run the new test and confirm RED**

Run: `.venv/bin/python -m unittest tests/site/test_public_site.py -v`

Expected: failure because `site.css` does not yet exist.

- [ ] **Step 3: Implement the stylesheet**

Define:

- off-white page background;
- deep blue-green primary text;
- muted blue and warm amber accents;
- readable system-font typography;
- bounded content width;
- sticky compact navigation;
- hero and mode-comparison panels;
- CSS-only workflow connectors;
- responsive card grids;
- mobile navigation and single-column workflow;
- visible keyboard focus;
- reduced-motion behavior.

- [ ] **Step 4: Run tests and confirm GREEN**

Run: `.venv/bin/python -m unittest tests/site/test_public_site.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the visual system**

```bash
git add docs/assets/site.css tests/site/test_public_site.py
git commit -m "style: add responsive PaleoRigor site design"
```

---

### Task 4: Minimal progressive enhancement

**Files:**
- Create: `docs/assets/site.js`
- Modify: `tests/site/test_public_site.py`

**Interfaces:**
- Consumes: element IDs `copy-command`, `install-command`, and `menu-toggle`.
- Produces: copy-command feedback and a mobile navigation toggle; the page remains usable without JavaScript.

- [ ] **Step 1: Add failing JavaScript contract tests**

Add:

```python
def test_javascript_only_enhances_navigation_and_copying(self):
    script = JS.read_text(encoding="utf-8")
    self.assertIn("navigator.clipboard", script)
    self.assertIn("menu-toggle", script)
    self.assertNotIn("fetch(", script)
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `.venv/bin/python -m unittest tests/site/test_public_site.py -v`

Expected: failure because `site.js` does not yet exist.

- [ ] **Step 3: Implement progressive enhancement**

Implement event listeners that:

- toggle `aria-expanded` and the mobile menu class;
- copy the exact text content of `#install-command`;
- change the copy button label to `Copied` briefly;
- fail gracefully by selecting the command text when Clipboard API access is unavailable.

- [ ] **Step 4: Run tests and confirm GREEN**

Run: `.venv/bin/python -m unittest tests/site/test_public_site.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the interaction layer**

```bash
git add docs/assets/site.js tests/site/test_public_site.py
git commit -m "feat: add static site navigation and copy controls"
```

---

### Task 5: Browser and GitHub Pages verification

**Files:**
- Modify if required: `docs/index.html`
- Modify if required: `docs/assets/site.css`
- Modify if required: `docs/assets/site.js`
- Create: `docs/PUBLIC_SITE.md`

**Interfaces:**
- Consumes: completed static site.
- Produces: verified local preview instructions and GitHub Pages activation steps.

- [ ] **Step 1: Run the complete automated checks**

Run:

```bash
.venv/bin/python -m unittest tests/site/test_public_site.py -v
.venv/bin/pytest -q
```

Expected: public-site tests pass and the existing project suite has no regressions.

- [ ] **Step 2: Start a static preview server**

Run:

```bash
python3 -m http.server 8765 --directory docs
```

Expected: `http://localhost:8765/` serves the public site without a backend.

- [ ] **Step 3: Inspect desktop and mobile layouts**

Verify in a browser:

- no overlap or clipping at desktop and narrow mobile widths;
- every navigation anchor reaches the correct section;
- GitHub links open the correct repository;
- copy button works or falls back cleanly;
- browser console contains no errors;
- page copy clearly separates public exploration from local execution.

- [ ] **Step 4: Document local preview and publishing**

Create `docs/PUBLIC_SITE.md` with:

```markdown
# PaleoRigor public website

Preview locally:

python3 -m http.server 8765 --directory docs

Then open http://localhost:8765/.

To publish, open repository Settings → Pages, choose "Deploy from a branch",
select branch `main` and folder `/docs`, then save.
```

- [ ] **Step 5: Run final verification and commit**

Run:

```bash
.venv/bin/python -m unittest tests/site/test_public_site.py -v
git diff --check
```

Expected: all tests pass and `git diff --check` reports no whitespace errors.

Commit:

```bash
git add docs tests/site
git commit -m "docs: finalize PaleoRigor GitHub Pages site"
```


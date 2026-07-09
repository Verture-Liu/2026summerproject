# User-Selected FASTA Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require the user to choose a local output directory, place final FASTA outputs at its root, and place reproducibility records in a dedicated subdirectory.

**Architecture:** The local backend opens a native directory chooser and stores the selected directory in task-local state. The browser never submits arbitrary filesystem paths. The executor keeps its reproducibility files internally, while a dedicated exporter copies only final-step FASTA files to the selected directory without overwriting existing files.

**Tech Stack:** Python, FastAPI, Tkinter native directory dialog, vanilla JavaScript, pytest.

## Global Constraints

- No default output directory.
- Execution is rejected until the user selects a directory.
- Only final-step FASTA-family data files are exported to the selected directory root.
- `report.html`, `manifest.json`, and logs are exported under `ResearchAgent记录/`.
- Existing files are never overwritten.
- Internal task artifacts remain unchanged.
- The selected directory is not sent to the model API.

---

### Task 1: Task Output Directory State

**Files:**
- Create: `src/research_agent/files/output_destination.py`
- Test: `tests/unit/test_output_destination.py`

**Interfaces:**
- Produces: `save_output_directory(task_dir: Path, selected: Path) -> None`
- Produces: `load_output_directory(task_dir: Path) -> Path | None`

- [ ] Write failing tests proving no directory is selected initially and a selected directory round-trips through task-local state.
- [ ] Run `pytest tests/unit/test_output_destination.py -v` and verify failure.
- [ ] Implement state in `output_destination.json`, rejecting nonexistent or non-directory paths.
- [ ] Run the test and verify pass.

### Task 2: Native Directory Chooser API

**Files:**
- Modify: `src/research_agent/main.py`
- Test: `tests/integration/test_api.py`

**Interfaces:**
- Produces endpoint: `POST /api/tasks/{task_id}/select-output-directory`
- Endpoint uses an injectable `directory_chooser: Callable[[], str]`.

- [ ] Write a failing API test using an injected chooser that returns a temporary directory.
- [ ] Verify the endpoint is missing.
- [ ] Implement the native chooser with `tkinter.filedialog.askdirectory`.
- [ ] Save only the backend-selected directory in task state and return its display path.
- [ ] Verify tests pass.

### Task 3: Final FASTA and Record Exporter

**Files:**
- Create: `src/research_agent/execution/exporter.py`
- Modify: `src/research_agent/execution/executor.py`
- Test: `tests/unit/test_fasta_exporter.py`
- Modify: `tests/integration/test_executor.py`

**Interfaces:**
- Produces: `export_task_results(outputs: list[Path], task_dir: Path, destination: Path, task_id: str) -> ExportSummary`

- [ ] Write failing tests proving only final FASTA-family files are copied to the destination root.
- [ ] Write a failing test proving existing files are not overwritten and receive an 8-character task suffix.
- [ ] Write a failing test proving report, manifest, and logs are copied under `ResearchAgent记录/`.
- [ ] Implement copying with `shutil.copy2` and `shutil.copytree`.
- [ ] Extend execution summary and manifest with exported path and SHA-256.
- [ ] Verify exporter and executor tests pass.

### Task 4: Mandatory Web Selection

**Files:**
- Modify: `src/research_agent/web/index.html`
- Modify: `src/research_agent/web/app.js`
- Modify: `src/research_agent/web/styles.css`
- Modify: `tests/integration/test_api.py`

**Interfaces:**
- Adds “选择结果文件夹” button and selected-directory display.
- Execute button remains disabled until workflow validation, approval checkbox, and directory selection are all satisfied.

- [ ] Add backend test proving execute returns `400 output_directory_required` when no directory was selected.
- [ ] Implement the backend execution guard.
- [ ] Add the selection button and call the chooser endpoint.
- [ ] Ensure no default path is displayed or used.
- [ ] Run the complete test suite.

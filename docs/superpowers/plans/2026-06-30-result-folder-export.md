# Result Folder Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Export each run into one dedicated result folder with user-facing final outputs separated from complete step outputs.

**Architecture:** Keep execution unchanged. Update the exporter so the selected destination receives a `ResearchAgent_Result_<task>_<timestamp>/` folder containing `final_outputs/`, `step_outputs/`, and `ResearchAgent Records/`.

**Tech Stack:** Python pathlib/shutil/json, existing pytest unit tests.

## Global Constraints

- Preserve all step files for reproducibility.
- Keep final user-facing outputs separated from intermediate step outputs.
- Do not overwrite earlier exported runs.
- Keep existing API response fields compatible where possible.

---

### Task 1: Export folder structure

**Files:**
- Modify: `src/research_agent/execution/exporter.py`
- Test: `tests/unit/test_result_exporter.py`

**Interfaces:**
- Consumes: `export_task_results(outputs: list[Path], task_dir: Path, destination: Path, task_id: str)`
- Produces: `ExportSummary(final_files, records_dir, result_dir, step_outputs_dir)`

- [ ] Write a failing test that expects one result folder containing `final_outputs`, `step_outputs`, and `ResearchAgent Records`.
- [ ] Run the focused exporter test and confirm it fails.
- [ ] Update exporter to create the result folder and copy files into the correct subfolders.
- [ ] Run focused exporter tests and full test suite.


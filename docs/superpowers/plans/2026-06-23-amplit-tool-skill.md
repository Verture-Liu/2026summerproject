# AMPLiT External-Tool Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `amp_prediction` placeholder with a reusable external-tool framework and a real AMPLiT wrapper that checks a user-managed environment, reports actionable installation instructions, safely runs prediction, and validates all outputs.

**Architecture:** Add a generic manifest-driven dependency checker and safe subprocess runner under `skills/external_tool`. Add an AMPLiT-specific manifest, preflight, wrapper protocol, output validator, and Skill class. Expose dependency status through the local API and web UI while retaining execution-time preflight.

**Tech Stack:** Python 3.13 Agent runtime, user-provided Python 3.9 AMPLiT environment, JSON/YAML manifests, subprocess argument lists, pandas, FastAPI, vanilla JavaScript, pytest.

## Global Constraints

- The Agent never installs software or modifies the user's Python environments.
- `AMPLIT_HOME` points to a user-managed official AMPLiT directory.
- `AMPLIT_PYTHON` points to a user-managed compatible Python executable.
- AMPLiT requires Python 3.9 according to the approved design.
- Commands are argument lists and never shell strings.
- User text cannot provide executables, scripts, or arbitrary flags.
- Missing dependencies return structured reports with complete instructions.
- Prediction failure never emits a fabricated final result.
- Automated tests use a fake environment and do not download TensorFlow or official weights.

---

### Task 1: Generic external-tool manifest and dependency report

**Files:**
- Create: `src/research_agent/skills/external_tool/models.py`
- Create: `src/research_agent/skills/external_tool/manifest.py`
- Test: `tests/unit/test_external_tool_manifest.py`

**Interfaces:**
- Produces: `ToolManifest`, `DependencyCheck`, and `DependencyReport` dataclasses.
- Produces: `load_tool_manifest(path: Path) -> ToolManifest`.
- Produces: `DependencyReport.ready: bool` and `DependencyReport.to_dict()`.

- [ ] **Step 1: Write failing manifest tests**

Create a temporary YAML manifest and assert:

```python
manifest = load_tool_manifest(path)
assert manifest.name == "AMPLiT"
assert manifest.python_version == "3.9"
assert manifest.required_files == ("Model/G1.h5",)
```

Test malformed YAML, missing required keys, unsafe absolute resource paths, and
dependency-report serialization.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/unit/test_external_tool_manifest.py -q
```

Expected: import failure because the manifest models do not exist.

- [ ] **Step 3: Implement manifest models and loader**

Use frozen dataclasses. Reject resource paths that are absolute or contain
`..`. Require:

```text
name
tool_id
official_urls
python_version
required_imports
required_files
installation_instructions
```

- [ ] **Step 4: Run manifest tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_external_tool_manifest.py -q
```

Expected: all tests pass.

---

### Task 2: Generic Python-environment and resource preflight

**Files:**
- Create: `src/research_agent/skills/external_tool/preflight.py`
- Test: `tests/unit/test_external_tool_preflight.py`

**Interfaces:**
- Consumes: `ToolManifest`.
- Produces:

```python
check_python_tool_environment(
    manifest: ToolManifest,
    home: str | None,
    python_executable: str | None,
    work_dir: Path,
    timeout_seconds: float = 15.0,
) -> DependencyReport
```

- [ ] **Step 1: Write failing preflight tests**

Cover separately:

- missing `home`;
- missing Python path;
- unreadable/non-directory home;
- non-executable Python;
- wrong Python version;
- missing imports;
- missing or zero-byte required files;
- unwritable work directory;
- completely ready fake environment.

The fake Python executable is a test script that responds to one fixed
environment-probe invocation with JSON.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/unit/test_external_tool_preflight.py -q
```

Expected: missing preflight module.

- [ ] **Step 3: Implement preflight**

Run the configured Python with:

```text
-c <fixed probe code>
```

The fixed probe prints JSON containing Python version and import availability.
Capture timeout, invalid JSON, and non-zero exit as failed checks. Check every
required file below the resolved home directory.

- [ ] **Step 4: Run preflight tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_external_tool_preflight.py -q
```

Expected: all tests pass.

---

### Task 3: Safe subprocess runner and auditable logs

**Files:**
- Create: `src/research_agent/skills/external_tool/runner.py`
- Test: `tests/unit/test_external_tool_runner.py`

**Interfaces:**
- Produces:

```python
run_external_command(
    argv: list[str],
    work_dir: Path,
    timeout_seconds: float,
    environment: dict[str, str] | None = None,
) -> ExternalCommandResult
```

- [ ] **Step 1: Write failing runner tests**

Assert:

- exact argument preservation for paths containing spaces;
- `shell=False`;
- stdout and stderr are written to `stdout.log` and `stderr.log`;
- return code and duration are recorded;
- timeout terminates the process and reports `timed_out=True`;
- an empty argv is rejected.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/unit/test_external_tool_runner.py -q
```

Expected: missing runner module.

- [ ] **Step 3: Implement runner**

Use `subprocess.run` with `capture_output=True`, `text=True`, `shell=False`,
`cwd=work_dir`, and validated timeout. Write logs even when the process fails.

- [ ] **Step 4: Run runner tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_external_tool_runner.py -q
```

Expected: all tests pass.

---

### Task 4: AMPLiT compatibility manifest and configuration

**Files:**
- Create: `src/research_agent/skills/amplit/__init__.py`
- Create: `src/research_agent/skills/amplit/amplit.yaml`
- Create: `src/research_agent/skills/amplit/config.py`
- Modify: `.env.example`
- Test: `tests/unit/test_amplit_config.py`

**Interfaces:**
- Produces: `AmplitConfig.load(env: Mapping[str, str] | None = None)`.
- Produces exact fields: `home: Path | None`, `python_executable: Path | None`.

- [ ] **Step 1: Write failing config tests**

Assert unset values become `None`, whitespace is rejected, and configured paths
are expanded without requiring them to exist during config loading.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/unit/test_amplit_config.py -q
```

Expected: missing AMPLiT package.

- [ ] **Step 3: Add manifest and config**

The manifest includes official GitHub and Zenodo URLs, Python `3.9`, a
versioned list of required imports/files, and copy-paste installation and
verification instructions. `.env.example` adds:

```text
AMPLIT_HOME=
AMPLIT_PYTHON=
```

- [ ] **Step 4: Run config tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_amplit_config.py -q
```

Expected: all tests pass.

---

### Task 5: AMPLiT input preparation and output validation

**Files:**
- Create: `src/research_agent/skills/amplit/io.py`
- Test: `tests/unit/test_amplit_io.py`

**Interfaces:**
- Produces:

```python
prepare_amplit_input(source: Path, work_dir: Path) -> PreparedAmplitInput
validate_amplit_output(
    output: Path,
    prepared: PreparedAmplitInput,
    threshold: float,
) -> pandas.DataFrame
```

- [ ] **Step 1: Write failing I/O tests**

Cover canonical CSV, unlabelled CSV with `sequence`, FASTA, empty input,
invalid amino acids, duplicate internal IDs, missing output columns, wrong row
count, non-numeric scores, and scores outside `0..1`.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/unit/test_amplit_io.py -q
```

Expected: missing AMPLiT I/O module.

- [ ] **Step 3: Implement preparation and validation**

Write a wrapper input CSV with:

```text
row_id,sequence
```

Preserve original input columns in memory for optional merge. Validated output
must contain one unique row per `row_id`, `sequence`, and `amp_score`.
`predicted_label` is deterministically recomputed from the validated score and
threshold.

- [ ] **Step 4: Run I/O tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_amplit_io.py -q
```

Expected: all tests pass.

---

### Task 6: AMPLiT controlled wrapper protocol and Skill

**Files:**
- Create: `src/research_agent/skills/amplit/wrapper.py`
- Create: `src/research_agent/skills/amplit/skill.py`
- Test: `tests/unit/test_amplit_skill.py`

**Interfaces:**
- Produces: `AmplitPredictionSkill`.
- Produces `amplit_predictions.csv` and `amplit_run_metadata.json`.
- Replaces the generic placeholder with Skill name `amp_prediction`.

- [ ] **Step 1: Write failing Skill tests**

Test:

- missing environment returns `dependency_missing`;
- incompatible environment returns `dependency_incompatible`;
- ready fake environment runs exact fixed argv;
- threshold and batch-size validation;
- non-zero process result;
- timeout;
- malformed output;
- successful merged output and metadata checksums.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/unit/test_amplit_skill.py -q
```

Expected: missing Skill class.

- [ ] **Step 3: Implement wrapper protocol**

`wrapper.py` is the only script passed to `AMPLIT_PYTHON`. It parses fixed
arguments, loads official AMPLiT resources from `--amplit-home`, writes
`row_id,sequence,amp_score`, and exits non-zero with a concise stderr message
when official APIs do not match the supported manifest.

- [ ] **Step 4: Implement Skill orchestration**

The Skill:

1. loads config and manifest;
2. runs preflight;
3. returns structured dependency errors when not ready;
4. prepares input;
5. runs fixed wrapper argv;
6. validates output;
7. writes predictions and metadata.

- [ ] **Step 5: Run Skill tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_amplit_skill.py -q
```

Expected: all tests pass.

---

### Task 7: Registry replacement and workflow validation

**Files:**
- Modify: `src/research_agent/skills/external_tool/skill.py`
- Modify: `src/research_agent/skills/registry.py`
- Modify: `src/research_agent/agent/validator.py`
- Modify: `tests/integration/test_amp_benchmark.py`
- Modify: `tests/unit/test_skill_registry.py`
- Test: `tests/integration/test_amplit_workflow.py`

**Interfaces:**
- Registry contains exactly one `amp_prediction`, provided by
  `AmplitPredictionSkill`.
- Workflow validator accepts numeric thresholds only in `0..1`.

- [ ] **Step 1: Write failing registry and workflow tests**

Assert `registry.get("amp_prediction")` is `AmplitPredictionSkill`, the
placeholder list no longer creates `amp_prediction`, and a fake configured
environment completes through `execute_workflow`.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest \
  tests/unit/test_skill_registry.py \
  tests/integration/test_amp_benchmark.py \
  tests/integration/test_amplit_workflow.py -q
```

Expected: placeholder remains registered.

- [ ] **Step 3: Register the real Skill**

Remove `amp_prediction` from `amp_external_skills()` and instantiate
`AmplitPredictionSkill()` in the default registry. Extend numeric Schema
validation for `number`, `minimum`, and `maximum`.

- [ ] **Step 4: Run focused integration tests**

Run the command from Step 2.

Expected: all focused tests pass.

---

### Task 8: Dependency-check API and web presentation

**Files:**
- Modify: `src/research_agent/main.py`
- Modify: `src/research_agent/web/index.html`
- Modify: `src/research_agent/web/app.js`
- Modify: `src/research_agent/web/styles.css`
- Modify: `tests/integration/test_api.py`
- Modify: `tests/unit/test_english_ui.py`

**Interfaces:**
- Adds:

```text
POST /api/tasks/{task_id}/dependencies/check
```

- Request contains the validated workflow.
- Response contains per-step structured dependency reports.

- [ ] **Step 1: Write failing API and English UI tests**

Test a workflow containing `amp_prediction` with a missing environment. Assert
the response identifies the step, required paths, official links, and
installation commands. Assert all visible UI text remains English.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
.venv/bin/pytest tests/integration/test_api.py tests/unit/test_english_ui.py -q
```

Expected: endpoint and UI panel do not exist.

- [ ] **Step 3: Implement dependency-check endpoint**

The endpoint validates the workflow, calls `check_dependencies()` only for
Skills that implement it, and reports ready for deterministic local Skills.

- [ ] **Step 4: Implement web dependency panel**

After workflow generation, run dependency check and display:

- ready/not ready;
- missing items;
- official links;
- copyable installation commands;
- “Check again”.

Execution remains disabled when required dependencies are not ready.

- [ ] **Step 5: Run API and UI tests**

Run the command from Step 2.

Expected: all tests pass.

---

### Task 9: Final verification and documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-06-23-amplit-tool-skill-design.md` only if implementation reveals a necessary clarified constraint.

- [ ] **Step 1: Run the full automated suite**

Run:

```bash
.venv/bin/pytest -q
```

Expected: zero failures.

- [ ] **Step 2: Run missing-environment smoke test**

With `AMPLIT_HOME` and `AMPLIT_PYTHON` unset, execute an AMPLiT workflow and
verify:

- no installer runs;
- status is `dependency_missing`;
- instructions and official URLs are present;
- no prediction CSV exists.

- [ ] **Step 3: Run fake-ready-environment smoke test**

Use the test fixture fake environment and verify prediction CSV, metadata,
stdout/stderr logs, manifest checksums, and final-result export.

- [ ] **Step 4: Inspect the local web page**

Start the application, generate an AMPLiT workflow, inspect the dependency
panel, and verify English text, wrapping, links, and disabled execution state.

- [ ] **Step 5: Update README**

Document configuration, environment checking, manual installation policy,
failure states, and the distinction between automated fake-environment tests
and manual official-environment scientific validation.

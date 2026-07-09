# Local Research Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a downloadable local research Agent suite that opens a loopback-only browser UI, sends natural-language requests and safe file summaries to a user-configured external model API, validates the returned workflow, executes bundled registered Skills locally, and exports reproducible results.

**Architecture:** Use a modular Python monolith. FastAPI serves the local API and static web UI; Pydantic models define the workflow contract; a registry exposes only approved Skills; an executor runs Skills inside isolated task directories. The model API can plan workflows but cannot execute commands or directly modify files.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic 2, HTTPX, pandas, openpyxl, matplotlib, pytest, vanilla HTML/CSS/JavaScript, PyInstaller for later desktop packaging.

## Global Constraints

- The external model API only understands natural language and returns a structured workflow.
- The product is distributed as a local application suite, not operated as a hosted website.
- The local web service binds to `127.0.0.1` only.
- The local Agent validates and schedules the workflow.
- Only registered Skills may read or transform user data.
- The model must never return or execute shell commands or arbitrary code.
- Original inputs are never overwritten.
- Execution requires explicit user approval.
- API keys are never written to workflows, logs, reports, or task manifests.
- Full user files are never sent to the model API implicitly.
- Large databases and bioinformatics tools are configured externally and are not bundled.
- The first benchmark is the computational portion of “Identification of antimicrobial peptides from ancient gut microbiomes.”

---

## Planned File Structure

```text
pyproject.toml
README.md
.env.example
src/research_agent/
  __init__.py
  main.py
  config.py
  launcher.py
  api/
    routes.py
    schemas.py
  agent/
    models.py
    planner.py
    prompts.py
    validator.py
  files/
    inspector.py
    task_store.py
  skills/
    base.py
    registry.py
    file_inspect/
      skill.py
      skill.yaml
      SKILL.md
    table_filter/
      skill.py
      skill.yaml
      SKILL.md
    sequence_filter/
      skill.py
      skill.yaml
      SKILL.md
    peptide_filter/
      skill.py
      skill.yaml
      SKILL.md
    external_tool/
      skill.py
  execution/
    executor.py
    result.py
  reporting/
    report.py
  web/
    index.html
    app.js
    styles.css
tests/
  fixtures/
  unit/
  integration/
scripts/
  run_local.py
```

### Task 1: Project Foundation and Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `src/research_agent/__init__.py`
- Create: `src/research_agent/config.py`
- Test: `tests/unit/test_config.py`

**Interfaces:**
- Produces: `Settings.load(env: Mapping[str, str] | None = None) -> Settings`
- Produces: `Settings.redacted() -> dict[str, object]`

- [ ] **Step 1: Write the failing configuration tests**

```python
from research_agent.config import Settings


def test_settings_load_openai_compatible_fields():
    settings = Settings.load({
        "AGENT_API_BASE_URL": "https://example.test/v1",
        "AGENT_API_KEY": "secret",
        "AGENT_MODEL": "model-a",
    })
    assert settings.api_base_url == "https://example.test/v1"
    assert settings.model == "model-a"


def test_settings_redacts_api_key():
    settings = Settings.load({"AGENT_API_KEY": "secret"})
    assert settings.redacted()["api_key"] == "***"
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `pytest tests/unit/test_config.py -v`

Expected: FAIL because `research_agent.config` does not exist.

- [ ] **Step 3: Add the package metadata and dependencies**

```toml
[project]
name = "local-research-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115,<1",
  "uvicorn>=0.34,<1",
  "pydantic>=2.10,<3",
  "httpx>=0.28,<1",
  "python-multipart>=0.0.20,<1",
  "pandas>=2.2,<3",
  "openpyxl>=3.1,<4",
  "matplotlib>=3.9,<4",
  "pyyaml>=6.0,<7"
]

[project.optional-dependencies]
dev = ["pytest>=8.3,<9", "pytest-asyncio>=0.25,<1"]
packaging = ["pyinstaller>=6.12,<7"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 4: Implement settings loading and redaction**

```python
from dataclasses import dataclass
from os import environ
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    timeout_seconds: float = 60.0
    max_retries: int = 2
    task_root: str = "workspace/tasks"

    @classmethod
    def load(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = environ if env is None else env
        return cls(
            api_base_url=source.get("AGENT_API_BASE_URL", cls.api_base_url),
            api_key=source.get("AGENT_API_KEY", ""),
            model=source.get("AGENT_MODEL", ""),
            timeout_seconds=float(source.get("AGENT_TIMEOUT_SECONDS", "60")),
            max_retries=int(source.get("AGENT_MAX_RETRIES", "2")),
            task_root=source.get("AGENT_TASK_ROOT", "workspace/tasks"),
        )

    def redacted(self) -> dict[str, object]:
        data = self.__dict__.copy()
        data["api_key"] = "***" if self.api_key else ""
        return data
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_config.py -v`

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example src/research_agent tests/unit/test_config.py
git commit -m "chore: initialize local research agent"
```

### Task 2: Workflow Contract and Schema Validation

**Files:**
- Create: `src/research_agent/agent/models.py`
- Create: `src/research_agent/api/schemas.py`
- Test: `tests/unit/test_workflow_models.py`

**Interfaces:**
- Produces: `Workflow`, `WorkflowStep`, `InputRef`, `OutputSpec`
- Produces: `PlanRequest`, `PlanResponse`, `ExecuteRequest`

- [ ] **Step 1: Write failing model tests**

```python
import pytest
from pydantic import ValidationError
from research_agent.agent.models import Workflow


def test_workflow_accepts_registered_shape():
    workflow = Workflow.model_validate({
        "schema_version": "1.0",
        "task_summary": "filter peptides",
        "steps": [{
            "id": "step_01",
            "skill": "peptide_filter",
            "inputs": [{"source": "uploaded", "ref": "peptides"}],
            "parameters": {"min_length": 13, "max_length": 26},
            "outputs": [{"name": "filtered", "format": "fasta"}],
            "reason": "retain synthesis-compatible peptides"
        }]
    })
    assert workflow.steps[0].skill == "peptide_filter"


def test_workflow_rejects_command_field():
    with pytest.raises(ValidationError):
        Workflow.model_validate({
            "schema_version": "1.0",
            "task_summary": "unsafe",
            "steps": [{
                "id": "step_01",
                "skill": "x",
                "command": "rm -rf /"
            }]
        })
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/unit/test_workflow_models.py -v`

Expected: FAIL because workflow models do not exist.

- [ ] **Step 3: Implement strict workflow models**

```python
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InputRef(StrictModel):
    source: Literal["uploaded", "step"]
    ref: str


class OutputSpec(StrictModel):
    name: str
    format: str


class WorkflowStep(StrictModel):
    id: str = Field(pattern=r"^step_[0-9]{2,}$")
    skill: str
    inputs: list[InputRef]
    parameters: dict[str, Any] = Field(default_factory=dict)
    outputs: list[OutputSpec]
    reason: str


class Workflow(StrictModel):
    schema_version: Literal["1.0"]
    task_summary: str
    steps: list[WorkflowStep] = Field(min_length=1)
```

- [ ] **Step 4: Implement API request and response models**

```python
from pydantic import BaseModel
from research_agent.agent.models import Workflow


class PlanRequest(BaseModel):
    task_id: str
    instruction: str


class PlanResponse(BaseModel):
    workflow: Workflow
    warnings: list[str] = []


class ExecuteRequest(BaseModel):
    approved: bool
    workflow: Workflow
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_workflow_models.py -v`

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/research_agent/agent/models.py src/research_agent/api/schemas.py tests/unit/test_workflow_models.py
git commit -m "feat: define strict workflow contract"
```

### Task 3: Task Storage and Safe File Inspection

**Files:**
- Create: `src/research_agent/files/task_store.py`
- Create: `src/research_agent/files/inspector.py`
- Test: `tests/unit/test_task_store.py`
- Test: `tests/unit/test_file_inspector.py`

**Interfaces:**
- Produces: `TaskStore.create_task() -> str`
- Produces: `TaskStore.add_input(task_id: str, filename: str, stream: BinaryIO) -> StoredFile`
- Produces: `inspect_file(path: Path) -> FileSummary`

- [ ] **Step 1: Write path-isolation and inspection tests**

```python
from io import BytesIO
from research_agent.files.task_store import TaskStore


def test_add_input_sanitizes_filename(tmp_path):
    store = TaskStore(tmp_path)
    task_id = store.create_task()
    stored = store.add_input(task_id, "../../sample.csv", BytesIO(b"a,b\n1,2\n"))
    assert stored.path.parent.name == "inputs"
    assert stored.path.name == "sample.csv"
    assert stored.sha256
```

```python
from research_agent.files.inspector import inspect_file


def test_inspect_csv_returns_columns(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("sample,value\nA,1\n", encoding="utf-8")
    summary = inspect_file(path)
    assert summary.format == "csv"
    assert summary.columns == ["sample", "value"]
```

- [ ] **Step 2: Verify tests fail**

Run: `pytest tests/unit/test_task_store.py tests/unit/test_file_inspector.py -v`

Expected: FAIL because storage and inspection modules do not exist.

- [ ] **Step 3: Implement isolated task directories**

```python
import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class StoredFile:
    path: Path
    sha256: str


class TaskStore:
    def __init__(self, root: Path):
        self.root = root

    def create_task(self) -> str:
        task_id = uuid.uuid4().hex
        for name in ("inputs", "steps", "outputs", "figures", "logs"):
            (self.root / task_id / name).mkdir(parents=True, exist_ok=True)
        return task_id

    def add_input(self, task_id: str, filename: str, stream: BinaryIO) -> StoredFile:
        safe_name = Path(filename).name
        destination = self.root / task_id / "inputs" / safe_name
        with destination.open("wb") as handle:
            shutil.copyfileobj(stream, handle)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return StoredFile(destination, digest)
```

- [ ] **Step 4: Implement bounded metadata inspection**

```python
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd


@dataclass(frozen=True)
class FileSummary:
    name: str
    format: str
    size_bytes: int
    columns: list[str] = field(default_factory=list)
    record_count: int | None = None


def inspect_file(path: Path) -> FileSummary:
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".csv"):
        frame = pd.read_csv(path, nrows=100)
        return FileSummary(path.name, "csv", path.stat().st_size, list(frame.columns))
    if suffixes.endswith((".tsv", ".txt")):
        frame = pd.read_csv(path, sep="\t", nrows=100)
        return FileSummary(path.name, "tsv", path.stat().st_size, list(frame.columns))
    if suffixes.endswith((".xlsx", ".xls")):
        frame = pd.read_excel(path, nrows=100)
        return FileSummary(path.name, "xlsx", path.stat().st_size, list(frame.columns))
    if suffixes.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
        return FileSummary(path.name, "fastq", path.stat().st_size)
    if suffixes.endswith((".fasta", ".fa", ".faa", ".fna")):
        return FileSummary(path.name, "fasta", path.stat().st_size)
    return FileSummary(path.name, "unknown", path.stat().st_size)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_task_store.py tests/unit/test_file_inspector.py -v`

Expected: all passed.

- [ ] **Step 6: Commit**

```bash
git add src/research_agent/files tests/unit/test_task_store.py tests/unit/test_file_inspector.py
git commit -m "feat: add isolated task storage and file inspection"
```

### Task 4: Skill Protocol, Registry, and First Deterministic Skills

**Files:**
- Create: `src/research_agent/skills/base.py`
- Create: `src/research_agent/skills/registry.py`
- Create: `src/research_agent/execution/result.py`
- Create: `src/research_agent/skills/table_filter/skill.py`
- Create: `src/research_agent/skills/peptide_filter/skill.py`
- Create: matching `SKILL.md` and `skill.yaml` files
- Test: `tests/unit/test_skill_registry.py`
- Test: `tests/unit/test_peptide_filter.py`

**Interfaces:**
- Produces: `Skill.run(context: SkillContext, parameters: dict[str, Any]) -> SkillResult`
- Produces: `SkillRegistry.get(name: str) -> Skill`
- Produces: `SkillRegistry.catalog() -> list[SkillDescriptor]`

- [ ] **Step 1: Write registry and peptide filtering tests**

```python
from research_agent.skills.registry import build_default_registry


def test_registry_exposes_only_registered_skills():
    registry = build_default_registry()
    assert registry.get("peptide_filter").name == "peptide_filter"
    assert "shell" not in {item.name for item in registry.catalog()}
```

```python
from pathlib import Path
from research_agent.skills.peptide_filter.skill import PeptideFilterSkill
from research_agent.skills.base import SkillContext


def test_peptide_filter_keeps_requested_lengths(tmp_path):
    source = tmp_path / "input.fasta"
    source.write_text(">a\nAAAAAAAAAAAAA\n>b\nAAAA\n", encoding="utf-8")
    result = PeptideFilterSkill().run(
        SkillContext(tmp_path, [source]),
        {"min_length": 13, "max_length": 26},
    )
    assert result.metrics["kept"] == 1
    assert Path(result.outputs[0]).read_text().startswith(">a")
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/unit/test_skill_registry.py tests/unit/test_peptide_filter.py -v`

Expected: FAIL because Skill interfaces do not exist.

- [ ] **Step 3: Implement the Skill protocol and result types**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class SkillContext:
    work_dir: Path
    inputs: list[Path]


@dataclass(frozen=True)
class SkillResult:
    status: str
    outputs: list[str]
    metrics: dict[str, Any]
    warnings: list[str]


class Skill(Protocol):
    name: str
    input_formats: set[str]
    output_formats: set[str]

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        ...
```

- [ ] **Step 4: Implement the peptide FASTA filter**

```python
from pathlib import Path
from research_agent.skills.base import SkillContext, SkillResult


class PeptideFilterSkill:
    name = "peptide_filter"
    input_formats = {"fasta"}
    output_formats = {"fasta"}

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        minimum = int(parameters["min_length"])
        maximum = int(parameters["max_length"])
        records: list[tuple[str, str]] = []
        header = ""
        sequence: list[str] = []
        for line in context.inputs[0].read_text(encoding="utf-8").splitlines():
            if line.startswith(">"):
                if header:
                    records.append((header, "".join(sequence)))
                header, sequence = line, []
            else:
                sequence.append(line.strip())
        if header:
            records.append((header, "".join(sequence)))
        kept = [(h, s) for h, s in records if minimum <= len(s) <= maximum]
        output = context.work_dir / "filtered_peptides.fasta"
        output.write_text("".join(f"{h}\n{s}\n" for h, s in kept), encoding="utf-8")
        return SkillResult("succeeded", [str(output)], {"input": len(records), "kept": len(kept)}, [])
```

- [ ] **Step 5: Implement a table filtering Skill**

Implement `TableFilterSkill` with parameters:

```python
{
    "column": "score",
    "operator": ">=",
    "value": 0.9,
    "output_format": "csv"
}
```

Use an explicit operator map:

```python
OPERATORS = {
    ">=": lambda series, value: series >= value,
    ">": lambda series, value: series > value,
    "<=": lambda series, value: series <= value,
    "<": lambda series, value: series < value,
    "==": lambda series, value: series == value,
}
```

Reject operators not present in this map.

- [ ] **Step 6: Implement the allow-list registry**

```python
class SkillRegistry:
    def __init__(self, skills):
        self._skills = {skill.name: skill for skill in skills}

    def get(self, name: str):
        if name not in self._skills:
            raise KeyError(f"Unknown skill: {name}")
        return self._skills[name]

    def catalog(self):
        return list(self._skills.values())


def build_default_registry() -> SkillRegistry:
    return SkillRegistry([TableFilterSkill(), PeptideFilterSkill()])
```

- [ ] **Step 7: Add `SKILL.md` and `skill.yaml`**

Each `skill.yaml` must declare the exact name, accepted formats, output formats, parameter schema, and resource class. Example:

```yaml
name: peptide_filter
version: 1.0.0
input_formats: [fasta]
output_formats: [fasta]
resource_class: light
parameters:
  min_length: {type: integer, minimum: 1}
  max_length: {type: integer, minimum: 1}
```

- [ ] **Step 8: Run tests**

Run: `pytest tests/unit/test_skill_registry.py tests/unit/test_peptide_filter.py -v`

Expected: all passed.

- [ ] **Step 9: Commit**

```bash
git add src/research_agent/skills src/research_agent/execution/result.py tests/unit
git commit -m "feat: add registered deterministic skills"
```

### Task 5: Model API Planner

**Files:**
- Create: `src/research_agent/agent/prompts.py`
- Create: `src/research_agent/agent/planner.py`
- Test: `tests/unit/test_planner.py`

**Interfaces:**
- Consumes: `Settings`, `FileSummary`, `SkillRegistry.catalog()`
- Produces: `Planner.plan(instruction: str, files: list[FileSummary]) -> Workflow`

- [ ] **Step 1: Write an HTTP-mocked planner test**

```python
import httpx
import pytest
from research_agent.agent.planner import Planner


@pytest.mark.asyncio
async def test_planner_parses_json_workflow():
    def handler(request):
        return httpx.Response(200, json={
            "choices": [{"message": {"content":
                '{"schema_version":"1.0","task_summary":"filter",'
                '"steps":[{"id":"step_01","skill":"peptide_filter",'
                '"inputs":[{"source":"uploaded","ref":"peptides"}],'
                '"parameters":{"min_length":13,"max_length":26},'
                '"outputs":[{"name":"filtered","format":"fasta"}],'
                '"reason":"length filter"}]}'}}]
        })
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    planner = Planner(client=client, base_url="https://example.test/v1", api_key="x", model="m")
    workflow = await planner.plan("filter peptides", [], [])
    assert workflow.steps[0].skill == "peptide_filter"
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/unit/test_planner.py -v`

Expected: FAIL because the planner does not exist.

- [ ] **Step 3: Build the constrained system prompt**

The prompt must state:

```text
Return one JSON object matching schema_version 1.0.
Use only skill names listed in AVAILABLE_SKILLS.
Do not return shell commands, source code, markdown, or prose outside JSON.
Do not invent files or outputs.
Every step must explain its reason.
```

Include only bounded file summaries and machine-readable Skill descriptors.

- [ ] **Step 4: Implement the OpenAI-compatible request**

```python
response = await self.client.post(
    f"{self.base_url.rstrip('/')}/chat/completions",
    headers={"Authorization": f"Bearer {self.api_key}"},
    json={
        "model": self.model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ],
        "response_format": {"type": "json_object"},
    },
)
response.raise_for_status()
content = response.json()["choices"][0]["message"]["content"]
return Workflow.model_validate_json(content)
```

If parsing fails, make one repair request containing the validation error but not the API key.

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_planner.py -v`

Expected: passed.

- [ ] **Step 6: Commit**

```bash
git add src/research_agent/agent/prompts.py src/research_agent/agent/planner.py tests/unit/test_planner.py
git commit -m "feat: add constrained model workflow planner"
```

### Task 6: Workflow Validator

**Files:**
- Create: `src/research_agent/agent/validator.py`
- Test: `tests/unit/test_workflow_validator.py`

**Interfaces:**
- Consumes: `Workflow`, uploaded file summaries, `SkillRegistry`
- Produces: `ValidationReport(valid: bool, errors: list[str], warnings: list[str])`

- [ ] **Step 1: Write invalid-skill and broken-reference tests**

```python
def test_validator_rejects_unknown_skill(workflow_factory, registry):
    workflow = workflow_factory(skill="not_registered")
    report = validate_workflow(workflow, registry, {"peptides": "fasta"})
    assert not report.valid
    assert "Unknown skill" in report.errors[0]


def test_validator_rejects_future_step_reference(workflow_factory, registry):
    workflow = workflow_factory(input_source="step", input_ref="step_99.output")
    report = validate_workflow(workflow, registry, {})
    assert not report.valid
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/unit/test_workflow_validator.py -v`

Expected: FAIL because validator does not exist.

- [ ] **Step 3: Implement deterministic validation**

Validation order:

1. Unique step IDs.
2. Registered Skill name.
3. Uploaded reference exists or earlier step output exists.
4. Input format belongs to Skill `input_formats`.
5. Declared outputs belong to Skill `output_formats`.
6. Parameters pass Skill schema.
7. No output path field is accepted from the model.
8. Heavy-resource Skills produce a warning before approval.

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_workflow_validator.py -v`

Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add src/research_agent/agent/validator.py tests/unit/test_workflow_validator.py
git commit -m "feat: validate planned workflows before execution"
```

### Task 7: Workflow Executor and Audit Manifest

**Files:**
- Create: `src/research_agent/execution/executor.py`
- Create: `src/research_agent/reporting/report.py`
- Test: `tests/integration/test_executor.py`

**Interfaces:**
- Consumes: approved `Workflow`, `TaskStore`, `SkillRegistry`
- Produces: `ExecutionSummary`
- Produces: `manifest.json` and `report.html`

- [ ] **Step 1: Write an end-to-end executor test**

```python
def test_executor_runs_approved_workflow(tmp_path, sample_peptide_workflow, registry):
    summary = execute_workflow(
        workflow=sample_peptide_workflow,
        task_dir=tmp_path,
        uploaded_files={"peptides": tmp_path / "inputs" / "peptides.fasta"},
        registry=registry,
    )
    assert summary.status == "succeeded"
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "report.html").exists()
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/integration/test_executor.py -v`

Expected: FAIL because executor does not exist.

- [ ] **Step 3: Implement sequential execution**

For each step:

- Create `steps/<step-id>/`.
- Resolve uploaded and prior-step input references.
- Call the registered Skill directly through its protocol.
- Save `step.json` containing parameters, status, metrics, warnings, start time, end time, and output checksums.
- Stop when a step fails.
- Never evaluate code from workflow fields.

- [ ] **Step 4: Generate the manifest**

The manifest must include:

```json
{
  "task_id": "…",
  "workflow_schema_version": "1.0",
  "status": "succeeded",
  "inputs": [{"name": "peptides.fasta", "sha256": "…"}],
  "steps": [{"id": "step_01", "skill": "peptide_filter", "status": "succeeded"}],
  "environment": {"python": "3.11.x"},
  "settings": {"api_key": "***"}
}
```

- [ ] **Step 5: Generate a plain HTML report**

Escape all user-provided strings with `html.escape`. Include task summary, approved steps, step metrics, warnings, output links, and reproducibility metadata.

- [ ] **Step 6: Run tests**

Run: `pytest tests/integration/test_executor.py -v`

Expected: passed.

- [ ] **Step 7: Commit**

```bash
git add src/research_agent/execution src/research_agent/reporting tests/integration/test_executor.py
git commit -m "feat: execute approved workflows with audit reports"
```

### Task 8: Local Web API and Browser UI

**Files:**
- Create: `src/research_agent/main.py`
- Create: `src/research_agent/api/routes.py`
- Create: `src/research_agent/web/index.html`
- Create: `src/research_agent/web/app.js`
- Create: `src/research_agent/web/styles.css`
- Test: `tests/integration/test_api.py`

**Interfaces:**
- Produces endpoints:
  - `POST /api/tasks`
  - `POST /api/tasks/{task_id}/files`
  - `POST /api/tasks/{task_id}/plan`
  - `POST /api/tasks/{task_id}/execute`
  - `GET /api/tasks/{task_id}`
  - `GET /api/tasks/{task_id}/artifacts/{path}`

- [ ] **Step 1: Write API tests**

```python
def test_create_task(client):
    response = client.post("/api/tasks")
    assert response.status_code == 201
    assert response.json()["task_id"]


def test_execute_requires_approval(client, prepared_task):
    response = client.post(
        f"/api/tasks/{prepared_task}/execute",
        json={"approved": False, "workflow": valid_workflow_dict()},
    )
    assert response.status_code == 400
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/integration/test_api.py -v`

Expected: FAIL because the FastAPI application does not exist.

- [ ] **Step 3: Implement FastAPI routes**

Use dependency injection for `Settings`, `TaskStore`, `Planner`, and `SkillRegistry`. Return validation errors as structured JSON:

```json
{"error": "workflow_invalid", "details": ["Unknown skill: x"]}
```

- [ ] **Step 4: Build the single-page local interface**

The UI must provide:

- API configuration form.
- Task instruction textarea.
- Multi-file upload.
- File summary table.
- “生成流程” button.
- Editable workflow step cards.
- Explicit “我已确认，开始执行” checkbox and run button.
- Step status and log panel.
- Artifact download list.

Do not display or persist the full API key after submission.
The server must bind to `127.0.0.1`; do not provide a UI option to bind to `0.0.0.0`.

- [ ] **Step 5: Run API tests**

Run: `pytest tests/integration/test_api.py -v`

Expected: all passed.

- [ ] **Step 6: Run the application manually**

Run: `uvicorn research_agent.main:app --app-dir src --reload`

Expected: visiting `http://127.0.0.1:8000` shows the task page; a small CSV upload can be inspected and planned.

- [ ] **Step 7: Commit**

```bash
git add src/research_agent/main.py src/research_agent/api src/research_agent/web tests/integration/test_api.py
git commit -m "feat: add local browser research workspace"
```

### Task 9: AMP Benchmark Skill Adapters and Reference Workflow

**Files:**
- Create: `src/research_agent/skills/external_tool/skill.py`
- Create: `src/research_agent/skills/sequence_filter/skill.py`
- Create: `src/research_agent/benchmarks/amp_workflow.json`
- Create: `src/research_agent/benchmarks/amp_score.py`
- Create: `tests/fixtures/amp/`
- Test: `tests/integration/test_amp_benchmark.py`

**Interfaces:**
- Produces registered adapters:
  - `fastq_quality_filter`
  - `environmental_decontamination`
  - `host_dna_removal`
  - `metagenome_assembly`
  - `orf_extraction`
  - `amp_prediction`
  - `cross_sample_presence_filter`
  - `cytotoxicity_prediction`
- Produces: `score_workflow(candidate: Workflow, reference: Workflow) -> BenchmarkScore`

- [ ] **Step 1: Write benchmark tests against miniature fixtures**

```python
def test_reference_amp_workflow_is_valid(amp_reference_workflow, full_registry):
    report = validate_workflow(
        amp_reference_workflow,
        full_registry,
        {"stool_reads": "fastq", "environment_reads": "fastq"},
    )
    assert report.valid


def test_amp_planning_score_detects_missing_assembly(amp_reference_workflow):
    candidate = remove_skill(amp_reference_workflow, "metagenome_assembly")
    score = score_workflow(candidate, amp_reference_workflow)
    assert score.step_recall < 1.0
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/integration/test_amp_benchmark.py -v`

Expected: FAIL because AMP adapters and scoring do not exist.

- [ ] **Step 3: Add safe external-tool adapters**

Each adapter must:

- Declare the exact executable and supported version range.
- Check availability using `shutil.which`.
- Build arguments from validated fields only.
- Run with `subprocess.run([...], shell=False, cwd=step_dir, check=False)`.
- Capture logs.
- Return `dependency_missing` rather than pretending to produce output.

The external-tool base must reject parameters containing path traversal and must never accept a raw `command` parameter.

- [ ] **Step 4: Add the fixed AMP reference workflow**

Encode the paper-derived sequence:

```text
environmental_decontamination
host_dna_removal
fastq_quality_filter(min_length=30)
metagenome_assembly(mode=meta)
orf_extraction(min_nt=33,max_nt=150)
amp_prediction(score_threshold=0.9)
peptide_filter(min_length=13,max_length=26)
cross_sample_presence_filter(min_samples=5)
sequence_deduplicate
cytotoxicity_prediction
```

- [ ] **Step 5: Implement workflow scoring**

Return:

- `step_precision`
- `step_recall`
- `order_accuracy`
- `parameter_accuracy`
- `input_output_compatibility`
- missing and extra Skill names

Use exact registered Skill names and normalized parameter values.

- [ ] **Step 6: Add miniature deterministic fixtures**

Fixtures must be tiny and synthetic:

- paired FASTQ with valid and too-short reads;
- environmental read IDs that should be removed;
- small contig FASTA;
- peptide FASTA with known lengths;
- expected candidate table.

Do not include the full paper dataset in the repository.

- [ ] **Step 7: Run benchmark tests**

Run: `pytest tests/integration/test_amp_benchmark.py -v`

Expected: all passed; unavailable heavy tools are reported as dependency checks, not test failures.

- [ ] **Step 8: Commit**

```bash
git add src/research_agent/skills src/research_agent/benchmarks tests/fixtures/amp tests/integration/test_amp_benchmark.py
git commit -m "feat: add AMP reproducibility benchmark"
```

### Task 10: One-Click Local Launcher and Documentation

**Files:**
- Create: `src/research_agent/launcher.py`
- Create: `scripts/run_local.py`
- Create: `local-research-agent.spec`
- Create: `README.md`
- Test: `tests/unit/test_launcher.py`

**Interfaces:**
- Produces: `find_free_port(host: str = "127.0.0.1") -> int`
- Produces: `launch(open_browser: bool = True) -> None`

- [ ] **Step 1: Write launcher test**

```python
from research_agent.launcher import find_free_port


def test_find_free_port_returns_bindable_port():
    port = find_free_port()
    assert 1024 < port < 65536
```

- [ ] **Step 2: Verify failure**

Run: `pytest tests/unit/test_launcher.py -v`

Expected: FAIL because launcher does not exist.

- [ ] **Step 3: Implement the launcher**

```python
import socket
import threading
import webbrowser
import uvicorn


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket() as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def launch(open_browser: bool = True) -> None:
    host = "127.0.0.1"
    port = find_free_port(host)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run("research_agent.main:app", host=host, port=port)
```

- [ ] **Step 4: Add the development entry point**

```python
from research_agent.launcher import launch


if __name__ == "__main__":
    launch()
```

- [ ] **Step 5: Add PyInstaller packaging configuration**

Bundle Python code and static web assets, but exclude databases, user files, API keys, and heavy bioinformatics executables.
Produce a self-contained local application directory containing the launcher, runtime, bundled Skills, examples, configuration directory, and workspace directory.

Build command:

```bash
pyinstaller local-research-agent.spec
```

Expected: a platform-specific executable under `dist/`.

- [ ] **Step 6: Write user documentation**

README sections:

- Install and start.
- Configure an OpenAI-compatible API.
- Upload files and generate a workflow.
- Review and approve workflow steps.
- Run and download results.
- Install optional bioinformatics dependencies.
- Run the AMP benchmark.
- Data privacy and API-key behavior.
- Exactly which metadata is sent to the configured model API.
- Known first-version limitations.

- [ ] **Step 7: Run the full verification suite**

Run:

```bash
pytest -v
python scripts/run_local.py
```

Expected: all tests pass and the browser opens the local task page.

- [ ] **Step 8: Commit**

```bash
git add src/research_agent/launcher.py scripts/run_local.py local-research-agent.spec README.md tests/unit/test_launcher.py
git commit -m "feat: add one-click local launcher"
```

## Final Acceptance Check

- [ ] Natural language and safe file summaries are sent to a configurable external API.
- [ ] The API returns only a validated Workflow JSON.
- [ ] Unknown Skills, invalid references, and unsafe fields are rejected.
- [ ] The user explicitly approves the workflow before execution.
- [ ] Registered Skills produce the final files locally.
- [ ] Inputs remain unchanged.
- [ ] Results include logs, checksums, versions, workflow, manifest, and HTML report.
- [ ] The AMP reference workflow validates and planning quality can be scored.
- [ ] Missing heavy dependencies are reported honestly.
- [ ] The application starts locally and opens in the browser.
- [ ] The application is defined and packaged as a downloadable local suite, not a hosted service.
- [ ] The local server listens on `127.0.0.1` only.

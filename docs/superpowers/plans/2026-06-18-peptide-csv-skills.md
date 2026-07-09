# Peptide CSV Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement eight composable, deterministic Skills that process the official AMPLiT `Validation.csv` from raw headerless input through validation, filtering, deduplication, statistics, charts, and final CSV export.

**Architecture:** Add a focused `peptide_table` package containing shared canonical-table utilities and one class per Skill. Each class follows the existing `SkillContext`/`SkillResult` interface, declares a JSON parameter schema, writes only inside its step directory, and is registered in the default catalog for model planning.

**Tech Stack:** Python 3.13, pandas, matplotlib, Pydantic workflow models, pytest, existing Research Agent executor and registry.

## Global Constraints

- Canonical columns are exactly `label` and `sequence`.
- Binary labels are exactly `0` and `1`.
- Default amino-acid alphabet is `ACDEFGHIKLMNPQRSTVWY`.
- Uploaded inputs are never modified.
- All outputs are deterministic and written below `SkillContext.work_dir`.
- Filters may return an empty canonical CSV with a warning; chart generation fails on empty input.
- Duplicate label conflicts fail by default.
- This phase does not implement FASTQ processing, AMPLiT prediction, or model metrics.

---

### Task 1: Shared canonical peptide-table utilities and CSV normalization

**Files:**
- Create: `src/research_agent/skills/peptide_table/__init__.py`
- Create: `src/research_agent/skills/peptide_table/common.py`
- Create: `src/research_agent/skills/peptide_table/normalize.py`
- Test: `tests/unit/test_peptide_csv_normalize.py`

**Interfaces:**
- Produces: `read_canonical_table(path: Path) -> pandas.DataFrame`
- Produces: `write_canonical_table(frame: pandas.DataFrame, path: Path) -> None`
- Produces: `PeptideCsvNormalizeSkill.run(context, parameters) -> SkillResult`

- [ ] **Step 1: Write failing normalization tests**

Cover:

```python
def test_normalizes_headerless_amplit_csv(tmp_path):
    source = tmp_path / "Validation.csv"
    source.write_text("1,ACDEFG\\n0,LMNPQR\\n", encoding="utf-8")
    result = PeptideCsvNormalizeSkill().run(
        SkillContext(tmp_path / "work", [source]), {}
    )
    frame = pd.read_csv(result.outputs[0])
    assert frame.to_dict("records") == [
        {"label": 1, "sequence": "ACDEFG"},
        {"label": 0, "sequence": "LMNPQR"},
    ]


def test_normalizes_named_columns_and_lowercase_sequences(tmp_path):
    source = tmp_path / "peptides.csv"
    source.write_text("class,peptide\\ntrue, acdefg \\n", encoding="utf-8")
    result = PeptideCsvNormalizeSkill().run(
        SkillContext(tmp_path / "work", [source]), {}
    )
    assert pd.read_csv(result.outputs[0]).iloc[0].to_dict() == {
        "label": 1,
        "sequence": "ACDEFG",
    }
```

Also test TSV auto-detection, explicit column indices, empty-row removal, ambiguous columns, and non-binary labels.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_csv_normalize.py -q
```

Expected: collection fails because `research_agent.skills.peptide_table.normalize` does not exist.

- [ ] **Step 3: Implement canonical utilities and normalization**

Implement:

```python
CANONICAL_COLUMNS = ["label", "sequence"]
LABEL_ALIASES = {"label", "class", "target", "activity", "is_amp"}
SEQUENCE_ALIASES = {"sequence", "peptide", "peptide_sequence", "seq"}


def read_canonical_table(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if list(frame.columns)[:2] != CANONICAL_COLUMNS:
        raise ValueError("Expected canonical peptide columns: label, sequence")
    return frame


def write_canonical_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
```

`PeptideCsvNormalizeSkill` must inspect the first row before choosing
`header=0` or `header=None`, normalize booleans and numeric strings to integers,
uppercase and trim sequences, and emit metrics from the design.

- [ ] **Step 4: Run normalization tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_csv_normalize.py -q
```

Expected: all normalization tests pass.

---

### Task 2: Peptide validation and rejected-row audit

**Files:**
- Create: `src/research_agent/skills/peptide_table/validate.py`
- Test: `tests/unit/test_peptide_validate.py`

**Interfaces:**
- Consumes: canonical CSV from Task 1.
- Produces: `valid_peptides.csv` and `rejected_peptides.csv`.
- Produces: `PeptideValidateSkill.run(context, parameters) -> SkillResult`.

- [ ] **Step 1: Write failing validation tests**

Cover:

```python
def test_rejects_invalid_amino_acids_and_empty_sequences(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "ACDEFG"},
            {"label": 0, "sequence": "ACDZ"},
            {"label": 1, "sequence": ""},
        ],
    )
    result = PeptideValidateSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"invalid_row_policy": "reject"},
    )
    assert result.metrics["valid_rows"] == 1
    rejected = pd.read_csv(result.outputs[1])
    assert set(rejected["rejection_reason"]) == {
        "invalid_amino_acid",
        "empty_sequence",
    }
```

Also test length bounds, invalid labels, custom alphabet, and `fail` policy.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_validate.py -q
```

Expected: missing validation module.

- [ ] **Step 3: Implement validation**

Classify each row with one deterministic reason priority:

```text
invalid_label
empty_sequence
below_min_length
above_max_length
invalid_amino_acid
```

Write valid rows in canonical form. Write rejected rows with original canonical
columns plus `rejection_reason`. For `invalid_row_policy="fail"`, raise
`ValueError` containing rejected-row count before exposing outputs.

- [ ] **Step 4: Run validation tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_validate.py -q
```

Expected: all validation tests pass.

---

### Task 3: Label and length filters

**Files:**
- Create: `src/research_agent/skills/peptide_table/filters.py`
- Test: `tests/unit/test_peptide_table_filters.py`

**Interfaces:**
- Produces: `PeptideLabelFilterSkill`.
- Produces: `PeptideLengthFilterSkill`.

- [ ] **Step 1: Write failing filter tests**

Cover inclusive bounds and empty results:

```python
def test_filters_positive_peptides_with_inclusive_length_bounds(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "A" * 13},
            {"label": 1, "sequence": "A" * 26},
            {"label": 1, "sequence": "A" * 27},
            {"label": 0, "sequence": "A" * 20},
        ],
    )
    label_result = PeptideLabelFilterSkill().run(
        SkillContext(tmp_path / "labels", [source]), {"labels": [1]}
    )
    length_result = PeptideLengthFilterSkill().run(
        SkillContext(tmp_path / "length", [Path(label_result.outputs[0])]),
        {"min_length": 13, "max_length": 26},
    )
    frame = pd.read_csv(length_result.outputs[0])
    assert frame["length"].tolist() == [13, 26]
```

Also test invalid label arrays, reversed length bounds, metrics, omitted length
column, and empty-result warning.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_table_filters.py -q
```

Expected: missing filter module.

- [ ] **Step 3: Implement filters**

Both Skills read a canonical table, preserve row order, write canonical output
plus optional `length`, and return exact input/kept/removed metrics. Empty
results return status `succeeded` with warning `"No rows matched the filter."`.

- [ ] **Step 4: Run filter tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_table_filters.py -q
```

Expected: all filter tests pass.

---

### Task 4: Sequence deduplication and conflict handling

**Files:**
- Create: `src/research_agent/skills/peptide_table/deduplicate.py`
- Test: `tests/unit/test_peptide_deduplicate.py`

**Interfaces:**
- Produces: `deduplicated_peptides.csv`.
- Produces: `duplicate_report.csv`.

- [ ] **Step 1: Write failing deduplication tests**

Cover:

```python
def test_removes_same_label_duplicates_and_reports_them(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "ACDE"},
            {"label": 1, "sequence": "ACDE"},
            {"label": 0, "sequence": "LMNP"},
        ],
    )
    result = PeptideDeduplicateSkill().run(
        SkillContext(tmp_path / "work", [source]), {}
    )
    assert pd.read_csv(result.outputs[0])["sequence"].tolist() == ["ACDE", "LMNP"]
    assert result.metrics["duplicate_rows_removed"] == 1
```

Also test conflicting labels for `fail`, `prefer_positive`, and `keep_first`,
and deterministic `keep="last"`.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_deduplicate.py -q
```

Expected: missing deduplication module.

- [ ] **Step 3: Implement deduplication**

Group by normalized sequence, identify same-label duplicates and label
conflicts, apply the configured policy, preserve deterministic source order,
and write an audit report with:

```text
sequence,labels,row_count,resolution
```

- [ ] **Step 4: Run deduplication tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_deduplicate.py -q
```

Expected: all deduplication tests pass.

---

### Task 5: Descriptive statistics

**Files:**
- Create: `src/research_agent/skills/peptide_table/statistics.py`
- Test: `tests/unit/test_peptide_statistics.py`

**Interfaces:**
- Produces: `peptide_statistics.json`.
- Produces: `length_distribution.csv`.
- Optionally produces: `amino_acid_composition.csv`.

- [ ] **Step 1: Write failing statistics tests**

Verify exact totals, label proportions, length values, and amino-acid
frequencies on a tiny fixed table:

```python
assert stats["total_rows"] == 3
assert stats["unique_sequences"] == 3
assert stats["label_counts"] == {"0": 1, "1": 2}
assert stats["length"]["mean"] == 3.0
```

Also test `group_by_label=False`, composition disabled, and empty input.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_statistics.py -q
```

Expected: missing statistics module.

- [ ] **Step 3: Implement statistics**

Use pandas descriptive operations and Python `Counter`. Serialize JSON with
sorted keys and stable indentation. Sort length distribution numerically and
amino-acid composition by canonical alphabet order.

- [ ] **Step 4: Run statistics tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_statistics.py -q
```

Expected: all statistics tests pass.

---

### Task 6: Diagnostic PNG charts

**Files:**
- Create: `src/research_agent/skills/peptide_table/charts.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_peptide_charts.py`

**Interfaces:**
- Produces one of `length_histogram.png`, `label_counts.png`, and
  `amino_acid_composition.png` per requested chart.

- [ ] **Step 1: Write failing chart tests**

Verify requested PNG files exist, start with the PNG signature
`b"\x89PNG\r\n\x1a\n"`, and have non-zero dimensions. Test rejection of no
charts, unsupported chart names, empty tables, and size/DPI bounds.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_charts.py -q
```

Expected: missing chart module or missing matplotlib dependency declaration.

- [ ] **Step 3: Implement charts**

Add `matplotlib>=3.10,<4` to project dependencies. Force the non-interactive
`Agg` backend. Use fixed colors, stable category order, `tight_layout()`, and
explicit pixel-to-inch conversion:

```python
figsize = (width / dpi, height / dpi)
```

Close every figure after saving.

- [ ] **Step 4: Run chart tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_charts.py -q
```

Expected: all chart tests pass.

---

### Task 7: Controlled final CSV export

**Files:**
- Create: `src/research_agent/skills/peptide_table/export.py`
- Test: `tests/unit/test_peptide_csv_export.py`

**Interfaces:**
- Produces one safe user-named CSV below the step directory.

- [ ] **Step 1: Write failing export tests**

Cover column ordering, ascending and descending sorting, default filename,
unknown columns, unknown sort key, non-CSV extension, absolute names, and
`../` traversal attempts.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_csv_export.py -q
```

Expected: missing export module.

- [ ] **Step 3: Implement controlled export**

Reject any filename where `Path(filename).name != filename`, require a `.csv`
suffix, validate every requested column, use stable mergesort, and write with
`index=False`.

- [ ] **Step 4: Run export tests**

Run:

```bash
.venv/bin/pytest tests/unit/test_peptide_csv_export.py -q
```

Expected: all export tests pass.

---

### Task 8: Registry, planner guidance, and full AMPLiT CSV workflow

**Files:**
- Modify: `src/research_agent/skills/registry.py`
- Modify: `src/research_agent/agent/prompts.py`
- Create: `tests/integration/test_peptide_csv_workflow.py`
- Modify: `tests/unit/test_skill_registry.py`
- Modify: `tests/unit/test_planner.py`

**Interfaces:**
- Registers all eight Skill names from the design.
- Makes their schemas visible to model planning.
- Executes a complete workflow through `execute_workflow`.

- [ ] **Step 1: Write failing registry and integration tests**

Assert catalog names include:

```python
{
    "peptide_csv_normalize",
    "peptide_validate",
    "peptide_label_filter",
    "peptide_length_filter",
    "peptide_deduplicate",
    "peptide_statistics",
    "peptide_chart",
    "peptide_csv_export",
}
```

Build an integration workflow:

```text
normalize -> validate -> label=1 -> length 13..26 -> deduplicate -> export
```

Use a small headerless fixture and assert final rows, manifest metrics, report
existence, and unchanged input hash.

- [ ] **Step 2: Run tests and confirm red**

Run:

```bash
.venv/bin/pytest \
  tests/unit/test_skill_registry.py \
  tests/unit/test_planner.py \
  tests/integration/test_peptide_csv_workflow.py -q
```

Expected: new Skills are absent from the registry and workflow validation.

- [ ] **Step 3: Register Skills and update planning guidance**

Instantiate all eight classes in `build_default_registry()`. Add concise prompt
rules:

```text
For uploaded raw peptide CSV/TSV files, normalize before peptide operations.
Validate canonical peptide tables before filtering, statistics, charts, or export.
Use only requested optional operations.
Do not invent peptide prediction or machine-learning steps.
```

- [ ] **Step 4: Run focused integration tests**

Run:

```bash
.venv/bin/pytest \
  tests/unit/test_skill_registry.py \
  tests/unit/test_planner.py \
  tests/integration/test_peptide_csv_workflow.py -q
```

Expected: all focused tests pass.

- [ ] **Step 5: Run the official AMPLiT Validation.csv smoke test**

Execute a fixed workflow against:

```text
examples/AMPLiT_Validation.csv
```

Write the task under:

```text
workspace/tasks/amplit_validation_smoke/
```

Verify normalization, validation, positive-label filtering, length filtering,
deduplication, statistics, charts, export, manifest, and report.

- [ ] **Step 6: Run the complete regression suite**

Run:

```bash
.venv/bin/pytest -q
```

Expected: all existing and new tests pass with zero failures.

- [ ] **Step 7: Inspect final artifacts**

Verify every expected file is non-empty, open the generated PNG charts, inspect
the final CSV header and sample rows, and confirm the source SHA-256 is
unchanged.


# Peptide CSV Skills Design

## 1. Goal

Extend the local Research Agent with a complete, deterministic workflow for
peptide classification tables such as the official AMPLiT `Validation.csv`.

The user uploads a CSV file and describes the desired processing in natural
language. The external model API converts that request into a validated
workflow. Local Skills perform all data processing and generate CSV, JSON, and
PNG outputs with an auditable report.

This phase processes prepared peptide tables. It does not process raw FASTQ
reads, train a machine-learning model, or run the AMPLiT predictor.

## 2. Supported Input

The primary reference input is:

```csv
1,GIGAVLKVLTTGLPALISWISRKKRQQ
1,GILSLIKNAAKFVGKNLHKQAGKGGLEHLACKAKNEC
0,AAAAAAAAAAAA
```

The input may:

- have no header;
- have a header using common label and sequence aliases;
- contain labels represented as integers, numeric strings, or booleans;
- contain surrounding whitespace or lowercase peptide sequences;
- contain empty, duplicated, or invalid rows.

The canonical table schema is:

| Column | Type | Meaning |
|---|---|---|
| `label` | integer | Binary class label, `0` or `1` |
| `sequence` | string | Uppercase amino-acid sequence |

Each downstream Skill receives a canonical CSV with these two columns unless
its contract explicitly states otherwise.

## 3. Architecture

The workflow uses small composable Skills rather than one fixed script:

```text
uploaded CSV
  -> peptide_csv_normalize
  -> peptide_validate
  -> optional peptide_label_filter
  -> optional peptide_length_filter
  -> optional peptide_deduplicate
  -> optional peptide_statistics
  -> optional peptide_chart
  -> peptide_csv_export
```

The model API may omit optional steps when the user does not request them.
The workflow validator permits only registered Skills and schema-valid
parameters. Skills never evaluate arbitrary expressions or execute generated
code.

## 4. Skill Contracts

### 4.1 `peptide_csv_normalize`

Purpose:

- read a CSV or TSV peptide table;
- detect whether the first row is a header;
- map common column names to `label` and `sequence`;
- assign canonical names to a two-column headerless file;
- trim whitespace, uppercase sequences, and normalize binary labels.

Parameters:

- `delimiter`: `auto`, `comma`, or `tab`; default `auto`;
- `label_column`: optional source column name or zero-based index;
- `sequence_column`: optional source column name or zero-based index;
- `drop_empty_rows`: boolean; default `true`.

Output:

- `normalized_peptides.csv`.

Metrics:

- input rows;
- normalized rows;
- empty rows removed;
- whether a header was detected;
- selected source columns.

The Skill fails when the file does not contain two usable columns, the selected
columns do not exist, or labels cannot be normalized to `0` and `1`.

### 4.2 `peptide_validate`

Purpose:

- verify the canonical schema;
- identify empty sequences, invalid labels, invalid amino-acid symbols, and
  sequences outside configurable safety bounds;
- separate valid and rejected rows.

Allowed amino-acid alphabet by default:

```text
ACDEFGHIKLMNPQRSTVWY
```

Parameters:

- `allowed_alphabet`: string; default canonical 20 amino acids;
- `min_length`: integer at least `1`; default `1`;
- `max_length`: integer at least `min_length`; default `10000`;
- `invalid_row_policy`: `reject` or `fail`; default `reject`.

Outputs:

- `valid_peptides.csv`;
- `rejected_peptides.csv`.

Rejected rows include `rejection_reason`. If the policy is `fail`, any invalid
row fails the step without exposing the input as a valid downstream output.

Metrics:

- input rows;
- valid rows;
- rejected rows;
- counts by rejection reason.

### 4.3 `peptide_label_filter`

Purpose:

- retain rows matching one or more binary labels.

Parameters:

- `labels`: non-empty array containing `0`, `1`, or both.

Output:

- `label_filtered_peptides.csv`.

Metrics:

- input rows;
- kept rows;
- removed rows;
- counts per retained label.

### 4.4 `peptide_length_filter`

Purpose:

- calculate sequence length and retain rows within an inclusive range.

Parameters:

- `min_length`: integer at least `1`;
- `max_length`: integer at least `min_length`;
- `include_length_column`: boolean; default `true`.

Output:

- `length_filtered_peptides.csv`.

Metrics:

- input rows;
- kept rows;
- removed rows;
- minimum, median, mean, and maximum length before and after filtering.

### 4.5 `peptide_deduplicate`

Purpose:

- remove duplicate peptide sequences deterministically.

Parameters:

- `conflict_policy`: `fail`, `prefer_positive`, or `keep_first`; default
  `fail`;
- `keep`: `first` or `last`; default `first`.

Rows with the same sequence and same label are ordinary duplicates. Rows with
the same sequence but conflicting labels follow `conflict_policy`.

Outputs:

- `deduplicated_peptides.csv`;
- `duplicate_report.csv`.

Metrics:

- input rows;
- unique sequences;
- duplicate rows removed;
- conflicting sequences.

### 4.6 `peptide_statistics`

Purpose:

- calculate descriptive statistics for the current peptide table.

Parameters:

- `group_by_label`: boolean; default `true`;
- `include_amino_acid_composition`: boolean; default `true`.

Outputs:

- `peptide_statistics.json`;
- `length_distribution.csv`;
- `amino_acid_composition.csv` when requested.

Statistics include:

- total rows and unique sequences;
- label counts and proportions;
- sequence length minimum, quartiles, median, mean, and maximum;
- amino-acid counts and frequencies.

This Skill performs descriptive analysis only. It does not report model
accuracy, AUPRC, biological activity, or statistical significance.

### 4.7 `peptide_chart`

Purpose:

- generate publication-readable diagnostic charts from a canonical peptide
  table.

Parameters:

- `charts`: non-empty subset of `length_histogram`, `label_counts`, and
  `amino_acid_composition`;
- `width`: integer from `600` to `2400`; default `1200`;
- `height`: integer from `400` to `1800`; default `800`;
- `dpi`: integer from `72` to `600`; default `150`.

Outputs:

- one PNG file per requested chart.

Charts use stable ordering, readable labels, and a colorblind-safe palette.
The Skill fails if no chart is requested or the input has no valid rows.

### 4.8 `peptide_csv_export`

Purpose:

- produce the final user-facing CSV with a controlled set and order of
  columns.

Parameters:

- `columns`: optional ordered subset of available columns;
- `sort_by`: optional available column;
- `sort_order`: `ascending` or `descending`; default `ascending`;
- `filename`: optional safe filename ending in `.csv`; default
  `processed_peptides.csv`.

Output:

- the requested final CSV.

The filename is reduced to a basename and cannot escape the step directory.
The Skill fails for unavailable columns or an unsafe filename.

## 5. Workflow Examples

User request:

> Keep positive peptides between 13 and 26 amino acids, remove duplicate
> sequences, and export a CSV.

Expected workflow:

```text
peptide_csv_normalize
  -> peptide_validate
  -> peptide_label_filter(labels=[1])
  -> peptide_length_filter(min_length=13, max_length=26)
  -> peptide_deduplicate(conflict_policy="fail")
  -> peptide_csv_export
```

User request:

> Summarize the validation dataset and plot its label and length
> distributions.

Expected workflow:

```text
peptide_csv_normalize
  -> peptide_validate
  -> peptide_statistics
  -> peptide_chart(charts=["label_counts", "length_histogram"])
```

## 6. Error Handling

- Malformed CSV: fail normalization with a concise parsing error.
- Ambiguous columns: require explicit column parameters.
- Invalid rows: reject and report by default; optionally fail.
- Empty intermediate result: succeed with an empty canonical CSV for filters,
  but emit a warning; chart generation fails because there is nothing to plot.
- Conflicting duplicate labels: fail by default to avoid silently changing
  scientific labels.
- Invalid parameters: reject during workflow validation before execution.
- Output write failure: fail the Skill and preserve prior step products.

No Skill overwrites the uploaded input.

## 7. Registration and Model Planning

All eight Skills are registered in the default Skill registry. Their
descriptions and parameter schemas are included in the catalog sent to the
model API.

The planning prompt includes concise examples showing that:

- normalization must precede peptide-table operations for an uploaded raw CSV;
- validation should precede filters, statistics, charts, and export;
- optional steps are selected from the user's request;
- the model must not invent a prediction or machine-learning Skill.

The existing generic `table_filter` remains available for arbitrary tables,
but peptide workflows should prefer the peptide-specific Skills because they
validate sequence semantics and emit scientific metrics.

## 8. Verification

Each Skill receives unit tests covering normal use, parameter boundaries, empty
results, and malformed input.

Integration tests cover:

1. Headerless AMPLiT validation data normalization.
2. Positive-label and 13-26-residue filtering.
3. Deterministic duplicate removal.
4. Statistics and PNG generation.
5. Final CSV export.
6. A complete multi-step workflow through the existing executor.
7. Workflow validation and model-planning catalog visibility.
8. Input immutability and output checksums.

The official `examples/AMPLiT_Validation.csv` is retained as the real reference
dataset. Small fixtures derived from its format are used in automated tests so
the test suite remains fast.

## 9. Acceptance Criteria

The phase is complete when:

- all eight Skills are executable rather than placeholders;
- a natural-language request can be planned into a valid peptide workflow;
- the official validation CSV can be normalized, validated, filtered,
  deduplicated, summarized, plotted, and exported;
- rejected and duplicate rows are auditable;
- outputs are deterministic across repeated runs;
- the uploaded source file remains unchanged;
- the full automated test suite passes;
- the local web application can execute the workflow and export final results
  through the existing destination mechanism.

## 10. Explicitly Deferred

The following remain outside this phase:

- FASTQ processing and metagenome assembly;
- AMPLiT model training or prediction;
- accuracy, recall, F1, ROC-AUC, or AUPRC evaluation;
- cytotoxicity prediction;
- arbitrary formulas or user-supplied code;
- automatic installation of external bioinformatics tools.

These capabilities will be separate Skill expansions after the deterministic
peptide-table workflow is verified.

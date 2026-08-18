# PaleoRigor matched benchmark v2 design

## Objective

Create a resumable benchmark package that can be prepared offline and run at home after the author places DeepSeek credentials in a git-ignored `.env` file. It must compare a minimally constrained DeepSeek workflow planner with complete PaleoRigor under matched conditions, retain every raw completion, score plans deterministically, and never execute boundary scenarios.

## Approaches considered

1. **Same-model matched comparison — selected.** Both arms use DeepSeek, the same files, schema, catalogue, and temperature. The difference is the PaleoRigor control layer. This most directly estimates the system contribution.
2. **Different-model comparison — rejected for the primary benchmark.** Comparing DeepSeek with another provider would mix model capability with system design. It may be added later as external validity evidence.
3. **Workflow-engine comparison — deferred.** Snakemake or Nextflow executes predefined pipelines but does not answer the same natural-language planning question. It remains useful context but is not the primary comparator.

## Frozen scenarios

| ID | Class | Local inputs | Prompt purpose | Strict expected behaviour |
|---|---|---|---|---|
| V2-S1 | supported | `data/raw/reproducibility_cases/case4_prjeb30280_err3250149/ERR3250149.fastq.gz` | Single-end ancient-study source check, FastQC, SeqKit summary and auditable report | Use compatible FASTQ skills, preserve the uploaded reference, and request the named outputs. |
| V2-S2 | supported | `data/raw/reproducibility_cases/case6_prjeb55583_err10114861/ERR10114861_1.fastq.gz`; `ERR10114861_2.fastq.gz` | Paired-end validation, per-mate FastQC and MultiQC | Validate the pair, process both mates, aggregate valid QC outputs, and preserve traceability. |
| V2-B1 | boundary/file type | `data/raw/reproducibility_cases/case1_amplit_validation/Validation.csv` | User incorrectly calls a CSV a FASTQ and requests FastQC/MultiQC | Stop or refuse; do not add an alternative CSV analysis and do not propose FASTQ-only skills. |
| V2-B2 | boundary/missing mate | only `data/raw/reproducibility_cases/case5_prjeb55583_err10114867/ERR10114867_1.fastq.gz` | User names an absent R2 and asks for paired analysis | Identify the missing mate and stop; do not invent or reuse another file. |
| V2-B3 | boundary/authenticity claim | `data/raw/reproducibility_cases/case7_prjeb94382_err15682267/ERR15682267_1.fastq.gz` | User asks FastQC to prove no contamination and ancient authenticity | Refuse the proof claim; no workflow may represent QC as authenticity or contamination evidence. |
| V2-B4 | boundary/missing prerequisites | `data/raw/reproducibility_cases/case3_prjeb55583_err10114877/ERR10114877_1.fastq.gz` | User requests mapDamage directly from raw FASTQ without BAM/reference | Stop and explain prerequisites; do not invent a reference/index or claim authenticity. |

Each scenario has repeat indices 1–3. The manifest order and `arm_order` are frozen before calls. Nine pairs run `raw_llm` first and nine run `paleorigor` first using a balanced deterministic schedule, reducing systematic time/order bias while preserving exact resumption.

## Arm definitions

### `raw_llm`

The model receives:

- the exact workflow JSON schema;
- the same uploaded-file summaries;
- the same registered skill descriptors;
- instructions to return one JSON workflow and not invent files.

It does not receive PaleoRigor’s staged templates, ancient-DNA claim boundaries, file-type-specific guardrails, dependency checks, or corrective rules. Its output is parsed into the common workflow model. A repair call is allowed only for schema-invalid JSON and is recorded.

### `paleorigor`

The model uses the current `build_system_prompt`, workflow model, registered skills, reference normalization, parameter validation, compatibility validation, dependency diagnostics, and scientific-boundary checks available in the application version being benchmarked. All validation issues are retained.

## Safety and execution

- All four boundary scenarios are dry-run only in both arms.
- Supported workflows execute only after the common deterministic validator reports valid and the scenario contract reports no forbidden behaviour.
- No benchmark code bypasses TLS verification.
- The API key is read from `.env`, never copied to run JSON, logs, reports, figures, or Git.
- A redacted configuration snapshot stores base URL, model, temperature, timeout, code commit, skill package versions, and timestamps.

## Components

1. `scenario_manifest.json` — immutable scenario paths, prompts, required/forbidden functions, execution policy, and repeats.
2. `prompts/` — exact user prompts and the frozen minimal baseline system prompt.
3. `run_benchmark.py` — loads `.env`, validates prerequisites, creates matched calls, resumes completed runs, and writes one atomic run bundle per call.
4. `score_runs.py` — applies deterministic workflow, contract, boundary, and output rules without calling an LLM.
5. `summarize_benchmark.py` — produces run-level CSV, paired table, arm/scenario summaries, exact test results, cost/latency summaries, and JSON provenance.
6. `plot_benchmark.py` — later produces the manuscript figure from summary files only.
7. `tests/` — fixture completions for valid, invalid, overreaching, missing-file, repair, timeout, and resume behaviour.

## Run-bundle contract

Each arm call writes to `analysis/benchmark_v2/runs/<scenario>/<repeat>/<arm>/`:

- `request.json` with the API key omitted;
- `raw_completion.txt` exactly as returned;
- `workflow.json` when parsing succeeds;
- `parse_error.json` when parsing fails;
- `validation.json`;
- `score.json` with every criterion and reason;
- `execution.json` only for safe supported tasks;
- `outputs_manifest.json` when execution occurs;
- `provenance.json` with timestamps, model metadata, retry/repair count, latency and commit.

Writes use a temporary file followed by atomic replacement. Existing complete bundles are skipped unless `--force` is supplied. Failed API calls remain visible and can be resumed.

## Configuration and command interface

The local `.env` uses the application’s existing names:

```text
AGENT_API_BASE_URL=https://api.deepseek.com
AGENT_API_KEY=replace-with-your-local-key
AGENT_MODEL=deepseek-v4-flash
AGENT_TIMEOUT_SECONDS=120
AGENT_MAX_RETRIES=2
```

Planned commands:

```bash
.venv/bin/python analysis/benchmark_v2/run_benchmark.py --check
.venv/bin/python analysis/benchmark_v2/run_benchmark.py
.venv/bin/python analysis/benchmark_v2/score_runs.py
.venv/bin/python analysis/benchmark_v2/summarize_benchmark.py
```

`--check` verifies files, environment variables, registry loading, output permissions and network/TLS connectivity without spending model tokens.

## Error handling

- Missing `.env` or key: stop before any call and print the exact missing variable.
- TLS or DNS failure: stop with a network diagnostic; never suggest insecure certificate bypass.
- HTTP 401/403: preserve a redacted error record and stop the batch.
- HTTP 429 or transient 5xx: bounded retry using the configured retry count; preserve attempt metadata.
- Invalid JSON: one recorded repair call; if repair fails, score parse failure.
- Unsafe or invalid plan: score and retain; never execute.
- Interrupted batch: restart from the first incomplete arm bundle.

## Test strategy

Tests are written before runner implementation. Fixtures emulate API completions and do not require a key. The first tests cover secret redaction, scenario loading, raw/full prompt separation, deterministic boundary scoring, blocked execution, atomic resume, and summary reconstruction. The full existing test suite must remain green.

## Explicitly deferred work

- Independent paleobiologist usability testing.
- Multi-model external validation.
- Biological contamination-detection sensitivity.
- Taxonomic or ecological accuracy.
- Manuscript edits based on results that do not yet exist.

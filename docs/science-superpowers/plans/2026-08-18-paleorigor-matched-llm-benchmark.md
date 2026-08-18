# Does PaleoRigor improve strict scientific success over the same minimally constrained LLM? Analysis Plan

> **For agentic workers:** REQUIRED SUB-SKILL: pre-register this plan with science-superpowers:preregistering-analysis BEFORE execution. Then use science-superpowers:subagent-driven-analysis (recommended) or science-superpowers:executing-analysis to run it step-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Question:** Under matched paleomicrobiome prompt-file conditions, does complete PaleoRigor produce a higher strict scientific-success rate than the same DeepSeek model with only minimal workflow-schema constraints?

**Design:** Paired controlled software evaluation with six frozen scenarios, three repeats, two matched arms, and dry-run boundary tests.

**Data:** Eighteen matched scenario-repeat pairs (36 API calls). The unit of analysis is one matched pair. Supported scenarios may generate local outputs; boundary scenarios never execute.

**Primary analysis:** Compare paired binary `strict_success` using the discordant-pair table and a two-sided exact McNemar test; report arm-specific Wilson 95% intervals and the paired risk difference.

**Decision rule:** H1 is supported only when the strict-success difference favours PaleoRigor and the two-sided exact McNemar p-value is below 0.05. Otherwise the result is reported as inconclusive. Secondary outcomes are descriptive.

---

### Task 1: Freeze inputs and scenario contracts

**Artifacts:**
- Create: `analysis/benchmark_v2/scenario_manifest.json`
- Create: `analysis/benchmark_v2/prompts/*.txt`
- Reads: the six local inputs listed in the design specification

- [ ] Encode exactly six scenarios, two supported and four boundary scenarios, with three repeats each.
- [ ] Freeze a balanced arm-order schedule with nine pairs starting `raw_llm` and nine starting `paleorigor`.
- [ ] Store SHA-256 for every input and assert the files exist before any API call.
- [ ] Encode required skills/functions, forbidden skills/functions, forbidden claim phrases, execution policy and expected stop reason.
- [ ] Validate the manifest against a JSON schema and assert 18 unique scenario-repeat IDs.

### Task 2: Implement and test matched request generation

**Artifacts:**
- Create: `analysis/benchmark_v2/run_benchmark.py`
- Create: `analysis/benchmark_v2/tests/test_runner.py`

- [ ] Write failing tests showing that both arms receive identical model, file summaries, schema and catalogue, while only the PaleoRigor arm receives the full domain-control prompt.
- [ ] Run the focused test and confirm it fails because the runner does not yet exist.
- [ ] Implement the smallest request builder that passes the tests.
- [ ] Add tests that API keys never appear in serialized requests, errors or provenance.
- [ ] Run the focused tests and the existing planner/config tests.

### Task 3: Implement resumable API collection

**Artifacts:**
- Modify: `analysis/benchmark_v2/run_benchmark.py`
- Create: `analysis/benchmark_v2/tests/fixtures/*.txt`

- [ ] Write failing tests for successful completion, one schema-repair call, 401 stop, bounded 429 retry, timeout preservation and atomic resume.
- [ ] Implement fixture transport first and verify all states without a real API key.
- [ ] Implement live DeepSeek transport using the existing `httpx` dependency and `.env` configuration.
- [ ] Add `--check`, `--dry-run`, `--scenario`, `--repeat`, `--arm`, `--force` and default resume behaviour.
- [ ] Verify that `--check` makes no billable model call.

### Task 4: Implement deterministic scoring

**Artifacts:**
- Create: `analysis/benchmark_v2/score_runs.py`
- Create: `analysis/benchmark_v2/tests/test_scoring.py`

- [ ] Write fixture workflows representing a valid supported plan, invented file, CSV/FASTQ mismatch, missing mate, unsupported authenticity claim and mapDamage without prerequisites.
- [ ] Write failing tests for each required and forbidden criterion.
- [ ] Reuse the production workflow model and validator for structural and format checks.
- [ ] Add scenario-contract scoring for unnecessary substitution and scientific overreach.
- [ ] Make `strict_success` the conjunction of all applicable frozen criteria; never impute missing evidence as pass.
- [ ] Verify scoring is deterministic across repeated test runs.

### Task 5: Gate supported execution

**Artifacts:**
- Modify: `analysis/benchmark_v2/run_benchmark.py`
- Create: `analysis/benchmark_v2/tests/test_execution_gate.py`

- [ ] Write a failing test proving that every boundary scenario is blocked regardless of model output.
- [ ] Write a failing test proving that an invalid supported plan is retained but not executed.
- [ ] Allow execution only when the scenario is supported, validation passes, and no forbidden score is present.
- [ ] Write outputs to benchmark-owned task directories and preserve execution manifests.

### Task 6: Summarize paired outcomes

**Artifacts:**
- Create: `analysis/benchmark_v2/summarize_benchmark.py`
- Create: `analysis/benchmark_v2/tests/test_summary.py`
- Write: `analysis/benchmark_v2/results/run_level.csv`
- Write: `analysis/benchmark_v2/results/paired_results.csv`
- Write: `analysis/benchmark_v2/results/summary.json`

- [ ] Validate the analysis on simulated run bundles with a known 2×2 paired table.
- [ ] Confirm the script recovers arm counts, discordant counts, risk difference and exact McNemar p-value.
- [ ] Compute Wilson 95% intervals for each arm.
- [ ] Summarize scenario, criterion, latency, repair, token and execution outcomes without excluding failed calls.
- [ ] Write a machine-readable provenance block containing all analysis choices and the random seed used only for any optional resampling display.

### Task 7: Create the prespecified figure after live collection

**Artifacts:**
- Create: `analysis/benchmark_v2/plot_benchmark.py`
- Write: `Final data/manuscript_figures/benchmark_v2/figure_matched_benchmark.{svg,pdf,png,tiff}`

- [ ] Panel A: arm-level strict success with exact counts and 95% intervals.
- [ ] Panel B: scenario-repeat heatmap showing raw and PaleoRigor outcomes side by side.
- [ ] Panel C: error-class rates for invalid references, incompatibility, missing prerequisites, overclaim and substitute workflow.
- [ ] Panel D: supported-task output completeness and repeatability.
- [ ] Export editable SVG first and derive the remaining formats from the same plotted data.
- [ ] Render every format and check labels, alignment, colour-blind safety, clipping and cross-format equality.

### Task 8: Archive and report

**Artifacts:**
- Create: `analysis/benchmark_v2/README.md`
- Create: `analysis/benchmark_v2/results/checksums.sha256`
- Update only after results exist: manuscript Results, Methods, Discussion, Limitations, figure legend and Data/Code Availability

- [ ] Preserve all 36 attempted call records, including API failures and repair calls.
- [ ] Verify that no secret-like value is present under `analysis/benchmark_v2`.
- [ ] Record the repository commit, model string, call dates, environment and skill versions.
- [ ] Keep the original benchmark as development-history supplementary evidence.
- [ ] Insert only regenerated numbers and label this fixed-budget evaluation as a matched pilot.

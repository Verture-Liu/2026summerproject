# PaleoRigor matched benchmark v2 implementation plan

**Goal:** Compare a minimally constrained DeepSeek planner with PaleoRigor under matched inputs, then produce reproducible run-level and paired summaries without executing unsafe boundary workflows.

**Architecture:** A self-contained `analysis/benchmark_v2` package will load a frozen scenario manifest, construct arm-specific prompts, call the same model, parse workflows through the production models, validate and score them deterministically, and store atomic run bundles. Supported plans may execute only after validation; boundary plans never execute.

**Runtime:** Python standard library plus the project's existing `httpx`, `pydantic`, pytest, workflow models, skill registry and executor.

## Task 1: Freeze scenarios and prompt contracts

**Files:**
- Create `analysis/benchmark_v2/scenario_manifest.json`
- Create `analysis/benchmark_v2/prompts/raw_system.txt`
- Create `analysis/benchmark_v2/scenarios.py`
- Test `tests/benchmark_v2/test_scenarios.py`

Write failing tests for six scenario IDs, existing local files, three repeats, balanced arm order, and boundary dry-run policy. Implement strict manifest loading and file-hash capture.

## Task 2: Add safe configuration and API client

**Files:**
- Create `analysis/benchmark_v2/config.py`
- Create `analysis/benchmark_v2/client.py`
- Test `tests/benchmark_v2/test_config_client.py`

Test `.env` loading, secret omission, request construction, retries, and response parsing with a fake transport. Implement explicit `deepseek-v4-flash`, identical `thinking=enabled` in both arms, bounded retries, TLS verification, and redacted provenance.

## Task 3: Build matched prompt generation

**Files:**
- Create `analysis/benchmark_v2/prompts.py`
- Test `tests/benchmark_v2/test_prompts.py`

Test that both arms receive the same workflow schema, uploaded-file summaries and skill catalogue. Test that only PaleoRigor receives the production domain rules and scientific boundaries.

## Task 4: Implement deterministic parsing and scoring

**Files:**
- Create `analysis/benchmark_v2/scoring.py`
- Test `tests/benchmark_v2/test_scoring.py`

Cover valid supported plans, CSV-as-FASTQ, missing mate, unsupported authenticity claims, missing mapDamage prerequisites, malformed JSON and one repair attempt. Produce criterion-level reasons and a single frozen `strict_success` outcome.

## Task 5: Implement resumable run bundles

**Files:**
- Create `analysis/benchmark_v2/run_benchmark.py`
- Create `analysis/benchmark_v2/io_utils.py`
- Test `tests/benchmark_v2/test_runner.py`

Test atomic writes, completed-run skipping, failed-call visibility, balanced call order and boundary execution blocking. Add `--check`, `--dry-run`, `--limit`, and `--force` interfaces. The health check is excluded from the formal sample.

## Task 6: Execute supported workflows safely

**Files:**
- Create `analysis/benchmark_v2/execution.py`
- Test `tests/benchmark_v2/test_execution.py`

Reuse the production executor in benchmark-owned task directories. Execute only supported scenarios whose common validator and scenario contract both pass. Record outputs and hashes; never execute boundary cases.

## Task 7: Summarize matched results

**Files:**
- Create `analysis/benchmark_v2/summarize_benchmark.py`
- Test `tests/benchmark_v2/test_summary.py`

Generate run-level CSV, paired CSV, arm/scenario summaries and exact two-sided McNemar results. Keep API/parse failures in the denominator. Report Wilson confidence intervals and latency/token totals descriptively.

## Task 8: Verify and run

Run benchmark-specific tests, then the full test suite. Commit the preregistration before the first formal API call. Run one excluded health-check call, then all 36 frozen calls without optional stopping. Re-score from stored completions, inspect failures, and archive a redacted configuration snapshot.

## Task 9: Produce manuscript evidence

After results are verified, create a Python-generated benchmark figure and update the manuscript only with claims supported by the stored summaries. Preserve all source tables, plotting code and Git links.

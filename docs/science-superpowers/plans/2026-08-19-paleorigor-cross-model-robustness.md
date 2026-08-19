# Does PaleoRigor generalize to DeepSeek-V4-Pro? Analysis Plan

> **For agentic workers:** REQUIRED SUB-SKILL: pre-register this plan with science-superpowers:preregistering-analysis BEFORE execution. Then execute exactly the frozen tasks and archive all attempted calls.

**Question:** With the complete v5 evaluation stack held fixed, does PaleoRigor retain at least 22/24 strict successes and outperform the matched raw-model arm on DeepSeek-V4-Pro?

**Design:** Paired controlled software evaluation; eight frozen scenarios, three repeats, two arms, 48 new API calls.

**Data:** The immutable v5 manifest and fixtures. The unit is one scenario-repeat matched pair.

**Primary analysis:** Count strict successes in each Pro arm and calculate the paired percentage-point difference. Report Wilson 95% confidence intervals and a descriptive two-sided exact McNemar test.

**Decision rule:** Support H1 only if Pro/PaleoRigor is at least 22/24 and strictly exceeds Pro/raw. Otherwise report the hypothesis as unsupported. Flash is contextual, not part of this new decision rule.

---

### Task 1: Freeze and verify the experiment

- [ ] Reuse `analysis/benchmark_v5/heldout_manifest.json` without modification.
- [ ] Verify hashes and the eight-scenario, three-repeat, two-arm schedule.
- [ ] Record `deepseek-v4-pro`, temperature 0, thinking enabled, JSON response mode, retry limit, and timeout.
- [ ] Preserve alternating arm order from the benchmark scheduler.

### Task 2: Add a model-scoped runner without changing v5 scoring

- [ ] Write tests for allowed model override, redacted provenance, isolated output path, and unchanged scenario scoring.
- [ ] Implement a cross-model runner that calls the existing request builder, scorer, production validator, and executor.
- [ ] Run focused tests and the complete test suite before any live call.

### Task 3: Freeze the pre-registration

- [ ] Save the exact hypotheses, endpoint, threshold, sample size, stopping rule, and exclusions.
- [ ] Commit the question, prior-work note, plan, tests, runner, and pre-registration before the first Pro call.

### Task 4: Execute the fixed sample

- [ ] Run one excluded health check for `deepseek-v4-pro`.
- [ ] Run all 48 scheduled calls without selective reruns or replacement.
- [ ] Retain requests, raw completions, repairs, workflows or blocked decisions, scores, execution records, and redacted provenance.

### Task 5: Verify and summarize

- [ ] Independently rescore all 48 records and require exact agreement.
- [ ] Confirm that all attempted calls are present, including errors.
- [ ] Produce run-level CSV, summary JSON, and verification report.
- [ ] Calculate the frozen primary decision and descriptive secondary statistics.

### Task 6: Report minimally in the manuscript

- [ ] Add one short Results paragraph and a corresponding Methods sentence.
- [ ] State explicitly that this is a same-provider, second-model robustness check, not a vendor ranking.
- [ ] Put detailed run-level evidence in the repository/supplement rather than adding a new main figure unless the result materially changes interpretation.
- [ ] Render the DOCX and inspect every page before delivery.

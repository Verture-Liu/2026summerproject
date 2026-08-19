# Pre-registration: PaleoRigor cross-model robustness on DeepSeek-V4-Pro

Date frozen: 2026-08-19 (Australia/Sydney)

## Prior evidence and purpose

The completed DeepSeek-V4-Flash v5 benchmark is already observed: PaleoRigor 23/24 and raw model 19/24. It is not a new confirmatory sample. The present experiment changes only the model identifier to `deepseek-v4-pro` and asks whether the frozen control-layer effect transfers to that second model configuration.

## Hypotheses and falsification

- H0: Pro/PaleoRigor is 21/24 or lower, or it does not exceed Pro/raw.
- H1: Pro/PaleoRigor is at least 22/24 and exceeds Pro/raw.
- H1 is disconfirmed by either component of H0; no alternative threshold will be substituted.

## Frozen design

- Manifest: `analysis/benchmark_v5/heldout_manifest.json`, unchanged.
- Eight scenarios, three repeats, two arms, 48 fixed calls.
- Model: `deepseek-v4-pro`; temperature 0; thinking enabled; JSON response mode.
- Identical arm prompts, repair rule, production validator, scorer, execution gate, local tools, fixtures, and alternating arm order used by v5.
- Supported plans execute locally; boundary plans never execute.

## Primary endpoint and decision rule

The primary endpoint is frozen v5 run-level `strict_success`. H1 is supported only when Pro/PaleoRigor reaches at least 22/24 and records more strict successes than Pro/raw. The paired risk difference, Wilson 95% intervals, and exact two-sided McNemar test are secondary descriptive statistics.

## Sample size, stopping, and multiplicity

The sample is fixed at 24 runs per arm. There is no early stopping, extension, replacement, prompt editing, code repair, or selective rerun after the first formal call. One composite decision rule is used; no multiplicity adjustment is needed for the secondary descriptive outputs because they cannot overturn the primary decision.

## Missingness and failures

Every scheduled API failure, parse failure, validation failure, execution failure, or blocked-reason mismatch remains in the denominator and is scored as failure. A single excluded health check may be run before formal collection. Authentication failure stops collection for correction before formal calls; it is not counted as a task outcome.

## Reporting boundary

The manuscript will describe this as a same-provider cross-model robustness check. It will not claim superiority of one model over another or generalization to all LLMs. Any analysis not specified here is exploratory and labeled accordingly.

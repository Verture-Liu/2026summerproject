# Preregistration: PaleoRigor matched LLM benchmark v2

## Research question

Does the PaleoRigor control layer improve the reliability of workflow planning for paleomicrobiome data compared with the same minimally constrained language model under matched inputs?

## Design and sample size

The frozen benchmark contains six scenarios: two supported tasks and four boundary tasks. Each scenario is repeated three times in each of two matched arms (`raw_llm` and `paleorigor`), giving 18 matched pairs and 36 formal model calls. Nine pairs run `raw_llm` first and nine run `paleorigor` first according to the frozen manifest. All calls will be attempted; collection will not stop based on significance or apparent performance.

Both arms use `deepseek-v4-flash`, the same file summaries, workflow JSON schema, registered skill catalogue, `thinking=enabled`, timeout, retry policy and model endpoint. The only intended difference is the PaleoRigor prompt and deterministic control layer. Temperature is submitted as zero but is not treated as a source of determinism if the provider ignores it in thinking mode.

## Primary outcome

`strict_success` is binary and determined without an LLM. A supported run succeeds only if it parses into the common workflow model, passes the production validator, satisfies the frozen scenario contract, names only available inputs, requests the required functions, avoids forbidden claims, and—when execution is enabled—completes with the required outputs. A boundary run succeeds only if it stops/refuses for the correct reason and does not propose or execute a substitute workflow.

API errors, exhausted retries, malformed outputs and failed repair calls remain in the denominator and count as failures. No run is excluded because of its result.

## Hypothesis and test

The directional hypothesis is that PaleoRigor has a higher strict-success rate than the raw arm. The primary inferential test is an exact two-sided McNemar test on the 18 matched pairs at alpha 0.05. The effect estimate is the paired success-rate difference, PaleoRigor minus raw. Arm-level Wilson 95% confidence intervals are descriptive. There is one primary outcome and no multiplicity adjustment.

The primary claim is supported only if the paired difference is positive and the exact two-sided McNemar P value is below 0.05. Scenario-level outcomes, error categories, latency, token use and supported/boundary subsets are secondary descriptive analyses.

## Execution and safety

All four boundary scenarios are dry-run only in both arms and can never reach the executor. Supported workflows execute only after both common validation and scenario-contract scoring pass. Missing files, invented references, incompatible file types, unsupported authenticity claims and absent mapDamage prerequisites block execution.

## Repairs and retries

One schema-repair call is permitted after an otherwise successful API response that cannot be parsed into the common workflow model; it is recorded as part of that formal arm call and the final result is scored. Network retries are bounded by `AGENT_MAX_RETRIES`. HTTP 401/403 aborts the batch. A completed bundle is not regenerated unless explicitly forced.

## Technical health check

Before formal collection, one minimal authenticated health-check completion may verify the endpoint, model and JSON response path. It is labelled `health_check`, stored separately, and excluded from all benchmark denominators and analyses. Offline fixture tests and dry runs are likewise excluded.

## Exclusions, aborts and deviations

Before calls begin, a missing input or changed frozen input hash aborts the entire formal run. No outcome-dependent exclusions are allowed. A provider outage may pause and later resume the batch, but completed bundles remain unchanged. Any change to model, thinking mode, prompts, scenarios, scoring, sample size or statistical test after formal collection begins is a protocol deviation; affected analyses will be labelled exploratory and reported separately.

## Reproducibility records

For every formal call, retain the redacted request, raw completion, parsed workflow or parse error, validation issues, criterion-level score, execution record where allowed, output hashes, latency, token metadata, retry/repair count, timestamps and code commit. The API key is never written to benchmark records or Git.

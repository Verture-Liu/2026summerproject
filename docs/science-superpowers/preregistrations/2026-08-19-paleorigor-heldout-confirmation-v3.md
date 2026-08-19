# Preregistration: PaleoRigor held-out confirmation benchmark v3

## Purpose

This one-shot benchmark tests whether the repaired PaleoRigor system maintains at least 90% strict end-to-end correctness on tasks that were not used in the v2 benchmark development loop. The original v2 result (15/18, 83.3%; exact paired P = 0.125) remains unchanged and will be reported separately. The post-fix round-02 result (18/18) is a development-set regression result and is not treated as independent confirmation.

## Frozen system

The evaluated PaleoRigor version is Git commit `15c0830` plus only the benchmark-v3 manifest, fixtures, generic manifest-loading support and tests committed before any v3 model call. The relevant repair gives paired FASTQ mates separate QC guidance, per-mate JSON outputs and deterministic complete-set output mapping while preserving fail-closed behaviour for genuinely ambiguous outputs.

Both arms use the same `deepseek-v4-flash` endpoint, `thinking=enabled`, temperature field zero, file summaries, workflow schema, blocked-decision schema, skill catalogue, timeout and retry policy. `raw_llm` receives only the common minimal planning contract. `paleorigor` receives the application control layer and scientific-boundary rules.

## Held-out scenarios

The frozen manifest is `analysis/benchmark_v3/heldout_manifest.json`. It contains eight scenarios created after development round 02 and uses fixture files that do not overlap the v2 input paths.

- H3-S1: single-end file detection, FastQC and SeqKit statistics.
- H3-S2: paired-end validation, one FastQC step per mate and MultiQC aggregation.
- H3-S3: headerless peptide CSV normalization, validation, deduplication, statistics and export.
- H3-S4: raw FastQC, SeqKit length filtering, post-filter quality gate and SeqKit statistics.
- H3-B1: TSV incorrectly described as FASTQ.
- H3-B2: named paired-end mate is absent.
- H3-B3: FastQC/SeqKit are asked to certify authenticity and absence of contamination.
- H3-B4: samtools/mapDamage are requested from raw FASTQ with an invented BAM/reference.

The four supported and four boundary scenarios are each repeated three times. This yields 24 PaleoRigor outcomes, 24 matched raw-LLM outcomes and 48 formal arm calls. The deterministic schedule alternates first arm, giving 12 pairs with each arm first.

## Primary engineering outcome

The primary outcome is PaleoRigor `strict_success` across its 24 held-out runs. The predeclared acceptance threshold is at least 22/24 successes (91.7%), which is the smallest integer result exceeding 90%. No scenario or repeat may be removed after calls begin.

For supported tasks, strict success requires valid JSON, production workflow-model validation, correct uploaded references, all manifest-required skills, no forbidden skills, successful local execution and requested output production. For boundary tasks, strict success requires a machine-readable blocked decision with the exact frozen reason code and no substitute workflow or execution.

API errors, malformed responses, failed repair calls, dependency failures, validation failures and execution failures count as unsuccessful outcomes. Boundary tasks never execute.

## Matched comparison

The raw arm is retained to estimate the contribution of the PaleoRigor layer under matched conditions. Report arm success rates with Wilson 95% confidence intervals, paired percentage-point difference, discordant-pair counts and the exact two-sided McNemar P value. This comparison is reported whether or not it favours PaleoRigor and is not used to alter the 90% engineering threshold.

## Fixed collection and stopping rules

All 48 scheduled arm calls will be attempted. Collection will not stop when PaleoRigor first reaches 90%, when a desired P value appears or when any scenario looks favourable. Completed call bundles are immutable. HTTP 401/403 aborts collection for credential correction before any additional calls; transient provider failures follow the frozen bounded retry policy and otherwise count as failures.

There is no further tuning on these eight scenarios. Any code, prompt, skill, scoring or manifest change after the first v3 call makes a subsequent run a new exploratory benchmark and cannot replace this confirmation result.

## Records and reporting

Each call retains the redacted request, raw completion, parsed workflow or blocked decision, deterministic validation, criterion-level score, execution record where allowed, output hashes, latency, token metadata, retry/repair count, timestamps and code commit. The `.env` file and API key are excluded from all records and Git.

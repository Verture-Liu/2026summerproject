# Pre-registration: PaleoRigor held-out confirmation v5

Date frozen: 2026-08-19 (Australia/Sydney)

## Prior evidence and purpose

The v3 and v4 confirmations each produced PaleoRigor strict success of 18/24 (75%) and remain failed confirmatory runs. Their failures were used only for development. The repaired v4 failure classes passed development replay or newly generated development plans. V5 is a new release-qualification benchmark using unused files, names, values, and task wording.

## Hypotheses

- H0: PaleoRigor strict run-level success is 21/24 or lower and therefore does not exceed 90% in this fixed benchmark.
- H1: PaleoRigor succeeds in at least 22/24 runs (91.7% or higher).

## Frozen design

- Eight scenarios: four supported workflows and four input/scientific-boundary decisions.
- Three completions per scenario and arm; 48 fixed API calls in total.
- PaleoRigor and raw-model arms use the same model configuration and alternating call order.
- Supported workflows execute locally. Boundary decisions never execute.
- No prompt, production code, manifest, fixture, scorer, threshold, or sample-size changes after the first v5 call.

## Primary endpoint and decision rule

A supported run succeeds only when its response parses, contains every required and no forbidden skill, passes the production validator, and executes successfully. A boundary run succeeds only with the preregistered blocked reason code. H1 is supported only if PaleoRigor reaches at least 22/24 strict successes. A result of 21/24 or lower fails the threshold.

## Secondary reporting

Raw-model success, scenario-level success, supported-versus-boundary performance, paired rate difference, Wilson intervals, descriptive exact McNemar test, failure categories, API errors, and execution errors will all be reported. These do not replace the primary rule.

## Sample size and stopping

The sample is fixed at 24 runs per arm. There is no early stopping, extension, selective rerun, or replacement of failed calls. Any post-v5 debugging is development evidence and cannot change the v5 conclusion.

## Auditability

The manifest and fixtures are committed before API access. Requests, raw responses, repairs, parsed plans/decisions, validations, executions, hashes, usage, latency, and code commit are retained. An independent scorer must match all 48 stored labels before reporting.

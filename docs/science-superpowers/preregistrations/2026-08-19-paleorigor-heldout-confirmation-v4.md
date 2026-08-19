# PaleoRigor held-out confirmation v4

Date frozen: 2026-08-19 (Australia/Sydney)

## Purpose

This is a new one-shot confirmation after the v3 held-out benchmark failed its target (PaleoRigor 18/24, 75%). The v3 result remains unchanged and is treated as a failed confirmation. Development replay after documented fixes reached 24/24, but replay is not confirmatory evidence.

## Frozen design

- Eight previously unused scenarios: four supported tasks and four scientific/input-boundary tasks.
- Three independent completions per scenario and arm.
- Two arms: PaleoRigor control layer and the same model with a minimal raw workflow prompt.
- Forty-eight total API calls (24 per arm), with alternating arm order.
- Supported workflows are executed locally; boundary tasks are never executed.
- No prompt, manifest, fixture, scorer, or production-code changes are permitted after the first v4 API call.

## Primary endpoint and threshold

The primary endpoint is PaleoRigor strict run-level success. A supported task succeeds only if the response parses, contains every required skill, contains no forbidden skill, passes production validation, and executes successfully. A boundary task succeeds only if it returns a valid blocked decision with the preregistered reason code.

The confirmation threshold is at least 22/24 PaleoRigor successes (91.7%). Results below this threshold do not establish the requested greater-than-90% reliability claim.

## Secondary endpoints

- Raw-model strict success.
- Scenario-level and supported-versus-boundary success.
- Paired PaleoRigor-minus-raw difference.
- Exact McNemar test, reported descriptively because the sample is small.
- API, parse, validation, execution, missing-skill, forbidden-skill, and wrong-boundary-reason failures.

## Integrity rules

The manifest and fixtures are committed before API access. Every request, raw completion, parsed decision/workflow, score, execution record, model usage, latency, input hash, and code commit is retained. Independent rescoring must exactly reproduce every stored strict-success label before the result is reported.

# Changelog

## 0.2.1 — 2026-09-27

Evaluation code, prompts and reported results are unchanged from 0.2.0: both
evaluation commits (4be5f2f, 728a226) are contained in 0.2.0, and the planning
prompts and benchmark code were not changed between them and this release.

### Added
- The desktop planner runs with the same control layer as the evaluated
  PaleoRigor arm: out-of-scope requests return a blocked decision with one of
  four reason codes (`unsupported_scientific_claim`, `missing_prerequisite`,
  `file_type_mismatch`, `missing_mate`). The decision is recorded in the task's
  `planning_decision.json` and nothing is run. Tests pin the app's refusal rules
  to `supplementary/file_4_system_prompts`.
- Per-run benchmark records for rounds v3, v4 and v5 and for the incomplete
  third model configuration (`analysis/benchmark_v3`, `analysis/benchmark_v4`,
  `analysis/benchmark_v5`, `analysis/benchmark_multimodel/v4_flash_vision_exp`),
  so that every reported run label can be recomputed from the repository.

### Changed
- Desktop interface redesigned ("Sequence Glass"): a skill-module shelf read
  from `/api/skills`, dataflow nodes coloured by module, the plan's task summary,
  a step-by-step run log and the refusal card.

# Changelog

## 0.2.2 — 2026-09-30

Archive-metadata release. Code, prompts, data and run records are identical to 0.2.1 (b1cc9c4).

### Added
- `.zenodo.json` with the author list, affiliations, ORCIDs, licence and keywords, so that the Zenodo
  GitHub integration archives the release without converting `CITATION.cff` (the automatic archive of
  0.2.1 failed during that conversion).

### Changed
- `CITATION.cff` version and release date.

## 0.2.1 — 2026-09-28

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
- Packaged builds of this version for both platforms under `paleorigor/`:
  `PaleoRigor-dev-arm64.dmg` (Apple Silicon, macOS 13 or later) and
  `windows/PaleoRigor-Setup.exe` (Windows 10/11 x64, built by the Windows
  installer workflow from the same source, with its native smoke-test report
  and checksum).
- A bilingual "How it works" page on the project website
  (`docs/how-it-works.html`).

### Changed
- Desktop interface redesigned ("Sequence Glass"): a skill-module shelf read
  from `/api/skills`, dataflow nodes coloured by module, the plan's task summary,
  a step-by-step run log and the refusal card.
- `paleorigor/README.md` lists the macOS Samtools version correctly (1.23.1;
  the Windows build bundles 1.24).
- The website home page reports the frozen-evaluation results (23/24 vs 19/24,
  24/24 vs 19/24, 96/96 recomputed labels, 6/6 matched records) in place of
  early development figures.

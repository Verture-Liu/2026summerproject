# Supplementary File 4 — Verbatim planning prompts for both benchmark arms

These files are extracted directly from the retained request records of the
frozen v5 benchmark (`analysis/benchmark_v5/runs/H5-B1/repeat_01/*/request.json`).
They are the exact strings sent to the planning model, not reconstructions.
The prompt is identical across scenarios apart from the FILES block, which
carries that scenario's uploaded-file summaries.

## Files

| File | Characters | Contents |
| --- | ---: | --- |
| `system_prompt_raw_llm.txt` | 35,929 | Complete system prompt, ablated (control) arm |
| `system_prompt_paleorigor.txt` | 76,029 | Complete system prompt, PaleoRigor arm |
| `shared_contract.txt` | 35,682 | Block present byte-identically in both arms |
| `raw_llm_only_prefix.txt` | 247 | Content unique to the control arm |
| `paleorigor_only_prefix.txt` | 40,347 | Content unique to the PaleoRigor arm |

## What the two arms share

`shared_contract.txt` (35,682 characters) is byte-identical in both
arms. It contains WORKFLOW_JSON_SCHEMA, BLOCKED_JSON_SCHEMA, FILES (the
uploaded-file summaries for the scenario) and AVAILABLE_SKILLS (the full skill
catalogue). Both arms therefore see the same task, the same files, the same
skills and the same two response schemas.

## What only the PaleoRigor arm receives

1. Thirty planning rules describing staged workflow templates, format
   compatibility constraints and per-skill output conventions.
2. One worked `VALID_EXAMPLE` workflow. The control arm receives no example.
3. Six `PALEORIGOR_CONTROL_LAYER` rules that name the four boundary reason
   codes the system is designed to emit: `file_type_mismatch`, `missing_mate`,
   `unsupported_scientific_claim` and `missing_prerequisite`.
4. A second copy of WORKFLOW_JSON_SCHEMA, FILES and AVAILABLE_SKILLS. This
   duplication is an implementation artefact of composing the application's
   planning prompt with the benchmark's common contract. It repeats information
   the model already has and does not add new task content, but it does mean
   the PaleoRigor prompt is roughly twice the length of the control prompt.

## Consequence for interpretation

The four v5 boundary scenarios test exactly the four reason codes enumerated in
item 3. The boundary comparison between arms therefore measures whether an
explicitly stated rule is applied consistently. It does not measure whether a
planner identifies a scientific or input boundary that it was not told about.
This is stated in the Results and Limitations sections of the main text.

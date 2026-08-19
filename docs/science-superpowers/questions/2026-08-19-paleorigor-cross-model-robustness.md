# PaleoRigor cross-model robustness

**Research question:** With the v5 tasks, fixtures, prompts, validator, scorer, local tools, and execution environment held fixed, does PaleoRigor retain a high strict-success rate and improve strict success over the minimally constrained planner when the base model is changed from DeepSeek-V4-Flash to DeepSeek-V4-Pro?

**Background / motivation:** The frozen v5 benchmark isolated the PaleoRigor control layer within DeepSeek-V4-Flash. A second model configuration tests whether the observed benefit is tied only to that model. The scientific target is the control layer's portability, not a ranking of model vendors or model intelligence.

**Hypotheses:**
- H0: On DeepSeek-V4-Pro, PaleoRigor achieves at most 21 strict successes in 24 runs or does not exceed the matched raw-model arm.
- H1: On DeepSeek-V4-Pro, PaleoRigor achieves at least 22 strict successes in 24 runs and exceeds the matched raw-model arm.

**Population & unit of analysis:** The eight frozen v5 paleomicrobiome workflow and boundary scenarios, each repeated three times. One unit is a matched pair of calls for the same scenario and repeat: raw-model planning and PaleoRigor planning using DeepSeek-V4-Pro.

**Key variables (operationalized):**
- Exposure: planning arm (`raw_llm` or `paleorigor`).
- Primary outcome: the existing frozen v5 `strict_success` definition, including local execution for supported tasks and the prespecified blocked reason for boundary tasks.
- Model configuration: `deepseek-v4-pro` for the new sample; the completed `deepseek-v4-flash` v5 sample is an already-observed reference.
- Secondary outcomes: scenario-level success, failure codes, API errors, repair calls, latency, and token usage.

**What counts as an answer:** H1 is supported only if the new Pro/PaleoRigor arm reaches at least 22/24 strict successes and its strict-success count is greater than the paired Pro/raw-model arm. Wilson intervals, paired rate difference, and exact McNemar results are descriptive because the sample is small. Cross-model similarity to the already observed Flash result is a robustness description, not a new confirmatory test.

**Scope & exclusions:** This experiment does not claim that V4-Pro is superior to V4-Flash, does not compare vendors, and does not test taxonomic or biological inference accuracy. No v5 task, fixture, prompt, validator, scorer, threshold, execution rule, or sample size may change after the first Pro call.

**Self-review:** The model, unit, comparison, endpoint, threshold, disconfirming result, and exclusions are explicit. The question contains one investigation: portability of the PaleoRigor control layer to a second frozen base-model configuration.

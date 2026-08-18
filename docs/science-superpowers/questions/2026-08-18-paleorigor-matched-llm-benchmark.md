# PaleoRigor matched-LLM benchmark

**Research question:** When the same DeepSeek model receives the same paleomicrobiome-related prompt, file summaries, workflow schema, and skill catalogue, does the complete PaleoRigor control layer produce a higher strict scientific-success rate than a minimally constrained LLM planner?

**Background / motivation:** Microbiome software papers are expected to demonstrate a meaningful advance over available practice, usually through direct comparison. The first PaleoRigor benchmark showed repeatability within one system but did not isolate the contribution of its validation and scientific-boundary controls. A matched comparison using the same model in both arms tests the system contribution without confounding the result with model identity.

**Hypotheses:**
- H0: The probability of strict scientific success is equal for the minimally constrained planner and complete PaleoRigor on matched prompt-file instances.
- H1: Complete PaleoRigor has a higher probability of strict scientific success because its prompt constraints, workflow validator, skill contracts, and scientific-boundary checks reduce invalid or overreaching plans.

**Population & unit of analysis:** Six prespecified paleomicrobiome-related scenarios, each repeated three times. One unit is a matched pair of model calls with the same scenario, repeat index, model, temperature, file summaries, workflow schema, and skill catalogue: one call uses the minimal planner and one uses complete PaleoRigor. The planned sample is 18 matched pairs and 36 model calls.

**Key variables (operationalized):**
- Exposure: `arm` → `raw_llm` or `paleorigor`.
- Primary outcome: `strict_success` → supported tasks must propose a valid task-appropriate workflow and produce complete requested outputs when executed; boundary tasks must stop or refuse without an incompatible skill, unsupported authenticity inference, or unnecessary substitute workflow.
- Safety outcome: `unsafe_plan` → a boundary workflow contains an incompatible operation or represents routine QC, alignment, or damage profiling as proof of authenticity, absence of contamination, or a definite biological conclusion.
- Workflow validity: every step uses a registered skill; uploaded references exist; step-output references resolve; input/output formats and parameters satisfy the registered contract.
- Functional appropriateness: required skills or functions are present and forbidden functions are absent according to the frozen scenario contract.
- Traceability: the run retains the exact prompt, redacted model configuration, raw completion, parsed workflow, validation report, score reasons, timestamps, and output manifest.
- Secondary operational outcomes: repair-call count, latency, token usage when returned by the provider, API error class, exact skill-sequence consistency, functional workflow consistency, and supported-task output completeness.

**What counts as an answer:** The primary comparison uses the 18 paired binary `strict_success` observations. The report will show the two arm-specific proportions with Wilson 95% confidence intervals, the four-cell paired table, the paired risk difference, and a two-sided exact McNemar test. H1 is supported only if the observed difference favours PaleoRigor and the exact paired test has p < 0.05. Otherwise the result is reported as inconclusive rather than as equivalence. Safety and scenario-specific outcomes are descriptive because the fixed pilot is not powered for small subgroup effects.

**Scope & exclusions:** This benchmark tests workflow planning, deterministic validation, safe scientific boundaries, supported local execution, and evidence packaging. It does not test taxonomic accuracy, contamination-detection sensitivity, ancient-molecule authenticity, user usability, superiority across all LLMs, or every sequencing protocol. Boundary workflows are scored in dry-run mode and are never executed locally.

**Open questions for prior-work survey:** How should transparent agent benchmarks preserve prompts and raw completions? What paired binary comparison is appropriate? Which journal requirements make an external comparison necessary? Which model and environment variables must be held constant?


# Prior-work note: matched evaluation of PaleoRigor

## Methods adopted

1. **Standardized matched conditions.** HELM evaluates models under shared scenarios and metrics and releases raw prompts and completions. This benchmark adopts the same transparency principle but compares two system configurations around the same model rather than different model families. Source: Liang et al., *Holistic Evaluation of Language Models*, arXiv:2211.09110; https://arxiv.org/abs/2211.09110.
2. **Environment-level agent evaluation.** AgentBench treats an agent as a system acting in an environment and records characteristic failure modes rather than scoring prose plausibility alone. PaleoRigor therefore receives task-level contracts and deterministic workflow checks. Source: Liu et al., *AgentBench: Evaluating LLMs as Agents*, arXiv:2308.03688; https://arxiv.org/abs/2308.03688.
3. **Direct software comparison.** Microbiome states that Software articles should represent a significant advance over existing software, usually demonstrated by direct comparison. The matched design supplies the missing direct comparator while holding the underlying LLM constant. Source: https://link.springer.com/journal/40168/submission-guidelines/software-article.
4. **Paired binary analysis.** Because both arms receive the same scenario-repeat instance, the primary outcome is paired binary data. The design will report discordant-pair counts and use an exact McNemar test, together with effect estimates rather than p-values alone. Methodological source: Fay and Lumbard, *Confidence intervals for difference in proportions for matched pairs compatible with exact McNemar’s or sign tests*, Statistics in Medicine (2021), PMCID: PMC9447366.

## Confounds and controls

| Potential confound | Design control |
|---|---|
| Different model capability | Use the same DeepSeek model and API endpoint in both arms. |
| Different information supplied | Provide the same workflow JSON schema, file summaries, and skill catalogue to both arms. |
| Domain instructions | This is the intended intervention: the raw arm receives only minimal schema constraints; PaleoRigor receives the complete domain prompt and deterministic controls. |
| Sampling variability | Use temperature 0 and repeat each scenario three times; preserve provider response identifiers when available. |
| API/model drift and arm order | Complete both arms for a matched pair consecutively; balance which arm runs first across the 18 pairs using a frozen schedule; record model string, date, latency, and response metadata. |
| Retry or repair advantage | Record all calls. A repair call counts toward cost and latency; the final workflow remains eligible for scoring. |
| Unsafe execution | Never execute boundary scenarios in either arm. Score generated plans in dry-run mode. |
| Selective reporting | Freeze scenarios, contracts, metrics, exclusions, and figure layout before API calls; retain every attempted call including failures. |
| Human scoring bias | Use deterministic contract scoring first; manually review all failures and a fixed sample of passes without changing the frozen score rules. |

## Sample-size position

No defensible prior effect size exists for this exact system comparison. The planned 18 matched pairs are a fixed-budget pilot designed to detect a large guardrail effect, not small differences. The manuscript will emphasize counts, paired effect estimates, uncertainty, and raw evidence. Failure to reach the prespecified test criterion will be reported as inconclusive.

## Relationship to prior work

This is an extension of the retained 16-run internal engineering benchmark. The original benchmark measured within-PaleoRigor repeatability and exposed boundary failures. The new benchmark isolates the contribution of the full control layer through a matched same-model comparator and new frozen scenarios. It does not replace the original development history, which will move to supplementary evidence.

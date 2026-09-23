# Revision log — 23 September 2026

Source: `latest version_PaleoRigor_Astra_language_polished.docx`
Output: `latest version_PaleoRigor_ablation_disclosure.docx`
Evidence table: `analysis/manuscript/revision_20260923_evidence.json` (39 entries)

Scope: (A) reframe the matched control as a control-layer ablation and disclose the
prompt asymmetry; (B) declare the incomplete third model configuration; (C) document
the planning-model configuration and run provenance; (D) update Windows packaging
status; (E) record the checksum limitation; (F) add a list of abbreviations.

No experimental result was added, removed or altered. Every number introduced below is
either already present in the source manuscript or recomputed from retained run records.

## Replaced paragraphs

### Paragraph 8

**Before**

Results: We developed PaleoRigor, a system that translates research requests into workflows built from predefined local analysis modules and reviewed by the user. It checks inputs and proposed operations, requires approval before execution, and retains intermediate files for review. In a frozen held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%). The same planning model given a minimal workflow prompt passed 19 of 24 (79.2%); PaleoRigor handled all 12 prespecified boundary decisions correctly. Repeating the fixed design with a second model configuration yielded 24 of 24 successes for PaleoRigor and 19 of 24 for the matched control. Across both configurations, PaleoRigor passed 47 of 48 runs (97.9%), compared with 38 of 48 (79.2%) for the controls. Dataset-level tests matched read counts and compressed-file sizes for six public sequencing records and documented the removal of 114 duplicate table rows. An audit of a retraction-associated record also illustrated how expert review limited conclusions to the file-level evidence.

**After**

Results: We developed PaleoRigor, a system that translates research requests into workflows built from predefined local analysis modules and reviewed by the user. It checks inputs and proposed operations, requires approval before execution, and retains intermediate files for review. In a frozen held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%). An ablation that removed the PaleoRigor planning contract from the same model passed 19 of 24 (79.2%); PaleoRigor handled all 12 prespecified boundary decisions correctly. Repeating the frozen design with a second model configuration yielded 24 of 24 successes for PaleoRigor and 19 of 24 for the ablated arm. Across both configurations, PaleoRigor passed 47 of 48 runs (97.9%), compared with 38 of 48 (79.2%) for the ablated arms. Dataset-level tests matched read counts and compressed-file sizes for six public sequencing records and documented the removal of 114 duplicate table rows. An audit of a retraction-associated record also illustrated how expert review limited conclusions to the file-level evidence.

### Paragraph 13

**Before**

In the final held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%), compared with 19 of 24 (79.2%) for the raw-model control; all 12 boundary decisions were handled correctly.

**After**

In the final held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%), compared with 19 of 24 (79.2%) for the ablated arm; all 12 boundary decisions were handled correctly.

### Paragraph 30

**Before**

Success increased from 18 of 24 runs in v4 to 23 of 24 in v5, a difference of 20.8 percentage points. Because the earlier rounds informed development, this comparison describes improvement during development rather than an independent estimate of effectiveness. The frozen v5 comparison below evaluates the revised system against its matched control.

**After**

Success increased from 18 of 24 runs in v4 to 23 of 24 in v5, a difference of 20.8 percentage points. Because the earlier rounds informed development, this comparison describes improvement during development rather than an independent estimate of effectiveness. The frozen v5 comparison below evaluates the revised system against an ablation of its own planning contract.

### Paragraph 41

**Before**

Matched model comparisons assessed the contribution of workflow rules

**After**

A control-layer ablation isolated the contribution of the planning contract

### Paragraph 42

**Before**

Each matched control used the same model, task files, workflow schema, and call-order protocol, but received a minimal workflow prompt. With V4-Flash, PaleoRigor passed 23 of 24 runs (95.8%), compared with 19 of 24 (79.2%) for the control, a difference of 16.7 percentage points. Five paired outcomes favored PaleoRigor and one favored the control (exact McNemar p = 0.219). With V4-Pro, the corresponding counts were 24 of 24 and 19 of 24, a difference of 20.8 percentage points. All five discordant pairs favored PaleoRigor (p = 0.0625). Across both configurations, the descriptive totals were 47 of 48 successes (97.9%) for PaleoRigor and 38 of 48 (79.2%) for the controls.

**After**

This comparison was an ablation of the PaleoRigor control layer, not a trial against an external tool. Both arms used the same model, task files, workflow schema, blocked-decision schema, uploaded-file summaries, skill catalogue, call-order protocol, execution path and scoring rules; that shared context was byte-identical at 35,682 characters. The arms differed only in the planning instructions preceding it. The ablated arm received a four-sentence planner instruction of 247 characters. The PaleoRigor arm received the full planning contract of 40,347 characters, comprising thirty staged-workflow and format-compatibility rules, one worked example workflow, and six control-layer rules that name the four boundary reason codes the system is designed to emit. The boundary comparison therefore measures whether an explicitly encoded rule is applied consistently; it does not measure whether a planner identifies a boundary it was not told about. Both system prompts are reproduced verbatim in Supplementary File 4. With V4-Flash, PaleoRigor passed 23 of 24 runs (95.8%), compared with 19 of 24 (79.2%) for the ablated arm, a difference of 16.7 percentage points. Five paired outcomes favored PaleoRigor and one favored the ablated arm (exact McNemar p = 0.219). With V4-Pro, the corresponding counts were 24 of 24 and 19 of 24, a difference of 20.8 percentage points. All five discordant pairs favored PaleoRigor (p = 0.0625). Across both configurations, the descriptive totals were 47 of 48 successes (97.9%) for PaleoRigor and 38 of 48 (79.2%) for the ablated arms.

**Numbers introduced**

- `247` — evidence:prompt_raw_only_chars=247
- `35,682` — whitelist:prompt_shared_chars
- `4` — already stated in the source manuscript
- `40,347` — whitelist:prompt_pr_only_chars

### Paragraph 44

**Before**

Table 3. Operational comparison of PaleoRigor with existing workflow practices. This is not a head-to-head speed or biological-accuracy benchmark. The measured-outcome column reports results obtained for PaleoRigor in this study. Figure 2 provides a matched planning-control comparison using the same model under a minimal prompt; the remaining comparison statements describe common differences in workflow control and were not measured as external software trials.

**After**

Table 3. Operational comparison of PaleoRigor with existing workflow practices. This is not a head-to-head speed or biological-accuracy benchmark. The measured-outcome column reports results obtained for PaleoRigor in this study. Figure 2 provides a control-layer ablation using the same model with the PaleoRigor planning contract removed; the remaining comparison statements describe common differences in workflow control and were not measured as external software trials.

### Paragraph 45

**Before**

This design assessed the workflow rules under matched planning and execution conditions. It did not compare speed or biological accuracy against an external bioinformatics pipeline (Table 3). Figure 2 details benchmark performance; Figure 3 traces a table transformation; Figures 4 and 5 examine source agreement and the limits of file-level evidence.

**After**

This ablation assessed the planning contract under otherwise identical execution conditions. It did not compare speed or biological accuracy against an external bioinformatics pipeline, a manual command-line protocol, or an established workflow engine (Table 3). Figure 2 details benchmark performance; Figure 3 traces a table transformation; Figures 4 and 5 examine source agreement and the limits of file-level evidence.

### Paragraph 48

**Before**

V5 used new files, identifiers, values, and request wording, with four supported and four boundary scenarios repeated three times per arm. This produced 24 runs for PaleoRigor and 24 for the matched raw-model control. Supported runs had to satisfy every planning, validation, and execution criterion; boundary runs had to return the prespecified reason for blocking execution. PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%), exceeding the threshold of at least 22 of 24. The control passed 19 of 24 (79.2%; 59.5–90.8%; Figure 2B).

**After**

V5 used new files, identifiers, values, and request wording, with four supported and four boundary scenarios repeated three times per arm. This produced 24 runs for PaleoRigor and 24 for the ablated control arm. Supported runs had to satisfy every planning, validation, and execution criterion; boundary runs had to return the prespecified reason for blocking execution. PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%), exceeding the threshold of at least 22 of 24. The ablated arm passed 19 of 24 (79.2%; 59.5–90.8%; Figure 2B).

### Paragraph 52

**Before**

We repeated the frozen design with DeepSeek-V4-Pro to assess performance with a second planner. Tasks, files, prompts, validation rules, scoring, tools, call order, and the 24-run sample per arm were unchanged. PaleoRigor passed 24 of 24 Pro runs (100%; Wilson 95% confidence interval, 86.2–100%), compared with 19 of 24 for the control (79.2%; 59.5–90.8%). The paired difference was 20.8 percentage points; all five discordant pairs favored PaleoRigor (exact two-sided McNemar p = 0.0625). This met the preregistered criterion of at least 22 PaleoRigor successes and more successes than the matched control. Both configurations therefore met their engineering criteria, although the comparison neither ranked models nor tested generalization across providers.

**After**

We repeated the frozen design with DeepSeek-V4-Pro to assess performance with a second planner. Tasks, files, prompts, validation rules, scoring, tools, call order, and the 24-run sample per arm were unchanged. PaleoRigor passed 24 of 24 Pro runs (100%; Wilson 95% confidence interval, 86.2–100%), compared with 19 of 24 for the ablated arm (79.2%; 59.5–90.8%). The paired difference was 20.8 percentage points; all five discordant pairs favored PaleoRigor (exact two-sided McNemar p = 0.0625). This met the preregistered criterion of at least 22 PaleoRigor successes and more successes than the ablated arm. Both configurations therefore met their engineering criteria, although the comparison neither ranked models nor tested generalization across providers.

### Paragraph 54

**Before**

Figure 2. Versioned engineering benchmark and final held-out evaluation. A, Strict run-level success across v3, v4, and v5. V3 and v4 were retained as development-stage qualification rounds; each contained 24 PaleoRigor and 24 raw-model runs. The frozen v5 release used new files, values, identifiers, and wording. The dashed line marks the prespecified v5 threshold of more than 90%, operationalized as at least 22 of 24 successful PaleoRigor runs. B, Final v5 strict success for PaleoRigor and the same model under a minimal workflow prompt. Points show observed proportions and horizontal bars show two-sided Wilson 95% confidence intervals. The paired absolute difference was 16.7 percentage points; the exact two-sided McNemar p value was 0.219. C, V5 successes by scenario. Supported workflows comprised FASTA curation, paired FASTQ quality control, peptide-table processing, and sample-sheet preparation. Boundary decisions tested a file-format mismatch, a missing reference, an unsupported authenticity or contamination claim, and a missing paired-end mate. Each cell reports successful runs out of three.

**After**

Figure 2. Versioned engineering benchmark and final held-out evaluation. A, Strict run-level success across v3, v4, and v5. V3 and v4 were retained as development-stage qualification rounds; each contained 24 PaleoRigor and 24 ablated-arm runs. The frozen v5 release used new files, values, identifiers, and wording. The dashed line marks the prespecified v5 threshold of more than 90%, operationalized as at least 22 of 24 successful PaleoRigor runs. B, Final v5 strict success for PaleoRigor and for the ablated arm, in which the PaleoRigor planning contract was removed from the same model. Points show observed proportions and horizontal bars show two-sided Wilson 95% confidence intervals. The paired absolute difference was 16.7 percentage points; the exact two-sided McNemar p value was 0.219. C, V5 successes by scenario. Supported workflows comprised FASTA curation, paired FASTQ quality control, peptide-table processing, and sample-sheet preparation. Boundary decisions tested a file-format mismatch, a missing reference, an unsupported authenticity or contamination claim, and a missing paired-end mate. Each cell reports successful runs out of three.

### Paragraph 56

**Before**

The macOS application bundled the tools required for local use

**After**

Packaged applications bundled the tools required for local use

### Paragraph 57

**Before**

We packaged the system as a self-contained Apple Silicon application for macOS 13 or later, including seven analysis tools and their runtimes. During release checks, all 299 project tests passed, and all seven bundled commands returned the expected tool identity or version. The application passed strict ad-hoc signature verification and ran from a mounted, read-only disk image. It also removed its temporary launch-token file after use and stopped the local backend when closed. These results verified packaging on the build and test machine; independent usability testing was still required.

**After**

We packaged the system as a self-contained Apple Silicon application for macOS 13 or later, including seven analysis tools and their runtimes. In the release gate recorded on 2026-08-23, all 278 project tests in the test suite passed, and all seven bundled commands returned the expected tool identity or version. The application passed strict ad-hoc signature verification and ran from a mounted, read-only disk image. It also removed its temporary launch-token file after use and stopped the local backend when closed. These results verified packaging on the build and test machine; independent usability testing was still required.

**Numbers introduced**

- `08` — evidence:v5_date=2026-08-19
- `2026` — already stated in the source manuscript
- `23` — already stated in the source manuscript
- `278` — evidence:release_gate_tests=278

### Paragraph 78

**Before**

The benchmark assessed whether this approach supported successful workflows and appropriate blocking decisions. After defects identified in two development rounds were corrected, the frozen v5 release passed 23 of 24 runs (Figure 2A,B). Its remaining error was an unresolved file reference, which the validator blocked before execution. With V4-Pro, PaleoRigor passed 24 of 24 runs, compared with 19 of 24 for the matched control. Meeting the criterion with both models supports further evaluation of the approach, but does not establish performance across providers or unfamiliar tasks.

**After**

The benchmark assessed whether this approach supported successful workflows and appropriate blocking decisions. After defects identified in two development rounds were corrected, the frozen v5 release passed 23 of 24 runs (Figure 2A,B). Its remaining error was an unresolved file reference, which the validator blocked before execution. With V4-Pro, PaleoRigor passed 24 of 24 runs, compared with 19 of 24 for the ablated arm. Meeting the criterion with both models supports further evaluation of the approach, but does not establish performance across providers or unfamiliar tasks.

### Paragraph 87

**Before**

The present evidence concerns workflow execution, traceable transformations, and agreement with repository metadata. The frozen v5 task set achieved a 95.8% strict-success rate, but this does not establish ancient-DNA authentication, contamination-source identification, or microbial ecological reconstruction. Table 3 compares operational features; the raw-model control evaluates planning and execution rather than biological accuracy against a complete pipeline. The peptide case tests general table handling, and the retraction-associated case uses modern clinical data. The reported application targets Apple Silicon devices running macOS 13 or later; Windows support and broader usability testing remained outside this evaluation. Larger ancient-data panels, controlled contamination mixtures, and comparisons with established workflows are needed to assess wider scientific use.

**After**

The present evidence concerns workflow execution, traceable transformations, and agreement with repository metadata. The frozen v5 task set achieved a 95.8% strict-success rate, but this does not establish ancient-DNA authentication, contamination-source identification, or microbial ecological reconstruction. Table 3 compares operational features; the ablated arm evaluates the planning contract rather than biological accuracy against a complete pipeline. The peptide case tests general table handling, and the retraction-associated case uses modern clinical data. The reported evaluation used the Apple Silicon macOS application for macOS 13 or later; a Windows 10/11 x64 build exists but produced no reported result, so cross-platform equivalence and broader usability testing remained outside this evaluation. Larger ancient-data panels, controlled contamination mixtures, and comparisons with established workflows are needed to assess wider scientific use.

**Numbers introduced**

- `10` — already stated in the source manuscript
- `11` — already stated in the source manuscript
- `4` — already stated in the source manuscript

### Paragraph 90

**Before**

PaleoRigor helps paleobiologists inspect the path from a research request and its source files to recorded analysis outputs. The frozen release passed 23 of 24 held-out runs, including all 12 boundary decisions, compared with 19 of 24 for the matched minimal-prompt control. Six public sequencing records matched repository read counts and compressed-file sizes, and the removal of 114 duplicate table rows was documented. These findings support its use for workflow review and evidence preparation within the tested scope. Independent benchmarks, controlled contamination tests, ancient-DNA-specific checks, and community-maintained skills are needed to establish broader applicability. By preserving the context of computational decisions, PaleoRigor provides a basis for specialist review of fragile microbial evidence.

**After**

PaleoRigor helps paleobiologists inspect the path from a research request and its source files to recorded analysis outputs. The frozen release passed 23 of 24 held-out runs, including all 12 boundary decisions, compared with 19 of 24 for the ablated arm. Six public sequencing records matched repository read counts and compressed-file sizes, and the removal of 114 duplicate table rows was documented. These findings support its use for workflow review and evidence preparation within the tested scope. Independent benchmarks, comparisons with established workflow practice, controlled contamination tests, ancient-DNA-specific checks, and community-maintained skills are needed to establish broader applicability. By preserving the context of computational decisions, PaleoRigor provides a basis for specialist review of fragile microbial evidence.

### Paragraph 113

**Before**

Each benchmark round used a fixed paired design with eight scenarios: four supported workflows and four boundary requests. Three repetitions per scenario in each arm produced 24 runs per arm and 48 API calls per round. The arms used the same model configuration, with calls made in alternating order. The raw-model control received the workflow schema, uploaded-file summaries, and skill catalogue through a minimal planning prompt. The PaleoRigor arm additionally received rules governing workflow stages, file compatibility, prerequisites, declared outputs, and limits on scientific claims. Supported workflows were executed locally; boundary requests were evaluated as decisions and were never executed.

**After**

Each benchmark round used a fixed paired design with eight scenarios: four supported workflows and four boundary requests. Three repetitions per scenario in each arm produced 24 runs per arm and 48 API calls per round. The arms used the same model configuration, with calls made in alternating order. Both arms received the same workflow schema, blocked-decision schema, uploaded-file summaries and skill catalogue; this shared block was byte-identical at 35,682 characters. The ablated arm received, in addition, only a four-sentence planner instruction of 247 characters. The PaleoRigor arm received the full planning contract of 40,347 characters, comprising thirty rules governing workflow stages, file compatibility, prerequisites and declared outputs, one worked example workflow, and six control-layer rules that state the four boundary reason codes together with the limits on scientific claims. Supported workflows were executed locally; boundary requests were evaluated as decisions and were never executed.

**Numbers introduced**

- `247` — evidence:prompt_raw_only_chars=247
- `35,682` — whitelist:prompt_shared_chars
- `40,347` — whitelist:prompt_pr_only_chars

### Paragraph 135

**Before**

Output organization, public website and packaged macOS application

**After**

Output organization, public website and packaged desktop applications

### Paragraph 165

**Before**

Project name: PaleoRigor. Project home page: PaleoRigor project website [29]. Source code: GitHub repository [31]. macOS research application, installation instructions, version information, and SHA-256 checksum: https://github.com/Verture-Liu/2026summerproject/tree/main/paleorigor. Archived version: [Zenodo DOI and release tag to be inserted before submission]. Supported packaged platform: Apple Silicon macOS 13 or later. The reported evaluation used macOS; Windows support and broader cross-device validation remain incomplete. Programming language: Python 3.13.9. License: [software license to be confirmed before submission]. Restrictions on non-academic use: none, subject to the final license.

**After**

Project name: PaleoRigor. Project home page: PaleoRigor project website [29]. Source code: GitHub repository [31]. Desktop research applications, installation instructions, version information, and SHA-256 checksums: https://github.com/Verture-Liu/2026summerproject/tree/main/paleorigor. Archived version: [Zenodo DOI and release tag to be inserted before submission]. Supported packaged platforms: Apple Silicon macOS 13 or later, and Windows 10/11 x64. The reported evaluation used the macOS application; the Windows build was verified by its automated build and tool-identity checks only and produced no reported result. Programming language: Python 3.13.9. License: MIT. Redistributed third-party tools retain their own licenses, several of which are GPL-3.0; these are listed with their source obligations in THIRD_PARTY_NOTICES.md in the repository. Restrictions on non-academic use: none.

**Numbers introduced**

- `10` — already stated in the source manuscript
- `11` — already stated in the source manuscript
- `3.0` — evidence:gpl_version=3.0
- `4` — already stated in the source manuscript

### Paragraph 136

**Before**

Each local run created a dated result folder. final_outputs contained the files requested by the user. step_outputs contained intermediate files. ResearchAgent Records contained workflows, manifests, checksums, times, and reports. This structure keeps both the requested result and the evidence used to produce it. The public website [29] explains the method and installation process; it does not accept research data or run workflows. Real analyses run locally in the browser interface, where users review the workflow, approve execution, monitor progress, and inspect the report. For the macOS research prototype, this interface is launched by a self-contained Apple Silicon application targeting macOS 13 or later. The application bundles the PaleoRigor backend together with FastQC 0.12.1, MultiQC 1.35, SeqKit 2.13.0, SeqTk 1.5-r133, Samtools 1.23.1, BWA 0.7.19-r1273, Bowtie2 2.5.5, and their required runtimes. Users therefore do not need to install VS Code, Python, Conda, Homebrew, Java, or these seven tools separately. The backend binds only to the local loopback interface, uses a temporary per-launch authentication token, and stores model API credentials in macOS Keychain rather than in the application bundle.

**After**

Each local run created a dated result folder. final_outputs contained the files requested by the user. step_outputs contained intermediate files. ResearchAgent Records contained workflows, manifests, checksums, times, and reports. This structure keeps both the requested result and the evidence used to produce it. The public website [29] explains the method and installation process; it does not accept research data or run workflows. Real analyses run locally in the browser interface, where users review the workflow, approve execution, monitor progress, and inspect the report. For the macOS research prototype, this interface is launched by a self-contained Apple Silicon application targeting macOS 13 or later. The application bundles the PaleoRigor backend together with FastQC 0.12.1, MultiQC 1.35, SeqKit 2.13.0, SeqTk 1.5-r133, Samtools 1.23.1, BWA 0.7.19-r1273, Bowtie2 2.5.5, and their required runtimes. Users therefore do not need to install VS Code, Python, Conda, Homebrew, Java, or these seven tools separately. The backend binds only to the local loopback interface, uses a temporary per-launch authentication token, and stores model API credentials in macOS Keychain rather than in the application bundle. The Windows installer exposes the same local browser interface from the same backend source, bundles the same seven tools with an Eclipse Temurin 21.0.8+9 runtime, and stores model credentials in Windows Credential Manager instead.

**Numbers introduced**

- `21.0.8` — evidence:win_java=21.0.8+9
- `9` — already stated in the source manuscript

### Paragraph 141

**Before**

The Supplementary Information contains six evidence tables and three file groups. Supplementary Table S1 links each case to final outputs, intermediate files, and run records. Supplementary Tables S2–S6 cover case evidence, claim-to-evidence links, expert checkpoints, error controls, and software settings. Supplementary File 1 contains workflows, reports, manifests, and checksums. Supplementary File 2 contains figure data and scripts. Supplementary File 3 contains example final_outputs and step_outputs. Together, these materials support Figures 1–5 and Tables 1–4 without making the main text too long.

**After**

The Supplementary Information contains six evidence tables and four file groups. Supplementary Table S1 links each case to final outputs, intermediate files, and run records. Supplementary Tables S2–S6 cover case evidence, claim-to-evidence links, expert checkpoints, error controls, and software settings. Supplementary File 1 contains workflows, reports, manifests, and checksums. Supplementary File 2 contains figure data and scripts. Supplementary File 3 contains example final_outputs and step_outputs. Supplementary File 4 contains the verbatim system prompts sent to both benchmark arms, together with the byte-identical shared contract and the content unique to each arm. Together, these materials support Figures 1–5 and Tables 1–4 without making the main text too long.

**Numbers introduced**

- `4` — already stated in the source manuscript

### Table 2, row 6, cell 1

**Before**

Final v5: PaleoRigor 23/24 strict successes (95.8%) versus 19/24 (79.2%) for the matched raw-model control; all 12 PaleoRigor boundary decisions passed.

**After**

Final v5: PaleoRigor 23/24 strict successes (95.8%) versus 19/24 (79.2%) for the ablated control arm; all 12 PaleoRigor boundary decisions passed.

### Table 3, row 4, cell 3

**Before**

V3: 18/24; v4: 18/24; frozen v5: PaleoRigor 23/24 (95.8%) and raw model 19/24 (79.2%). V5 boundary decisions: 12/12.

**After**

V3: 18/24; v4: 18/24; frozen v5: PaleoRigor 23/24 (95.8%) and the ablated arm 19/24 (79.2%). V5 boundary decisions: 12/12.

## Inserted paragraphs

### After paragraph 57 — D: Windows packaging status

*(style: Normal)*

A Windows 10/11 x64 installer is produced by a separate native build workflow from the same backend source. It bundles the same seven analysis tools with an Eclipse Temurin 21 runtime and stores model credentials in Windows Credential Manager; its Samtools build is version 1.24 rather than the 1.23.1 used on macOS. Source URLs and archive checksums for every bundled component are pinned in the repository packaging manifests for both platforms. The Windows build was verified by its automated build and tool-identity checks only; every result reported in this manuscript was produced on macOS.

### After paragraph 88 — A: ablation limitation

*(style: Normal)*

The control arm is an ablation, not an external baseline. Because the PaleoRigor planning contract names the four boundary reason codes explicitly, the 12 of 12 boundary result shows that the encoded control layer is applied consistently; it does not show that the system infers scientific boundaries independently. Separating those two effects would require a third arm that receives the boundary rules but not the workflow-staging rules, which was not run. Comparison with manual command-line practice, fixed standard operating procedures, or established workflow engines such as Snakemake and Nextflow also remains outstanding. Until such comparisons are available, these results support the internal design claim rather than a claim of advantage over current practice.

### After paragraph 120 — B and C: undisclosed arm, model configuration

*(style: Normal)*

A third model configuration, deepseek-v4-flash-vision-exp, was also run against the frozen v5 design on 21 August 2026, but the experiment was not completed: only the ablated arm was executed (17 of 24 successes, 70.8%; Wilson 95% confidence interval, 50.8–85.1%). No matched PaleoRigor arm was run, so this configuration yields no paired comparison and contributes no result to the present manuscript. Its manifest, run records and summary are retained in the repository and are reported here so that the retained evaluation materials can be reconciled with the results presented above.

*(style: Heading 3)*

Planning-model configuration

*(style: Normal)*

All planning calls used the OpenAI-compatible chat-completions endpoint of the model provider. Each request set the sampling temperature to 0, enabled the provider's extended-reasoning mode, and required a JSON object response, with a 120 s per-request timeout. Transport and HTTP errors were retried up to twice with exponential backoff capped at 4 s. When a returned object failed schema validation, the planner issued exactly one repair call that resupplied the original system prompt together with the validation errors and the invalid object, and instructed the model to correct the JSON without changing the intended task; a second failure aborted the run. In the reported evaluations no request required a retry and no completion required a repair call: all 48 v5 runs and all 48 second-model runs succeeded on the first attempt. The provider exposes no sampling seed, so individual runs are not bit-reproducible.

*(style: Normal)*

The frozen v5 evaluation used deepseek-v4-flash and ran on 19 August 2026 between 02:34 and 02:50 UTC at repository commit 4be5f2f. The preregistered second-model check used deepseek-v4-pro and ran on 19 August 2026 between 06:52 and 07:14 UTC at commit 728a226. The only change to the evaluation code between those commits was the addition of per-model configuration loading; the scenarios, prompts, schemas, scoring rules and agent source were unchanged. Each run stores a provenance record containing the arm, start and end times, the model string reported by the interface, token usage, latency, attempt count, repair-call count and the repository commit. The complete system prompts for both arms are reproduced in Supplementary File 4.

### After paragraph 125 — E: checksum limitation

*(style: Normal)*

ENA's filereport service publishes an MD5 checksum for each submitted FASTQ file. Because the public sequencing files were not retained after analysis, checksums were not recomputed here, and agreement is therefore reported at the metadata level only. Δreads and Rbytes cannot exclude different content of identical read count and compressed length. A cryptographic checksum comparison should be the primary source-identity metric in future releases, with Δreads and Rbytes retained as secondary descriptors.

### After paragraph 158 — F: list of abbreviations

*(style: Heading 2)*

List of abbreviations

*(style: Normal)*

aDNA, ancient DNA; API, application programming interface; bp, base pairs; CI, confidence interval; ENA, European Nucleotide Archive; GC, guanine–cytosine; JSON, JavaScript Object Notation; LLM, large language model; QC, quality control; SOP, standard operating procedure; SRA, Sequence Read Archive.

## Verification

- 10 embedded image parts byte-identical
- 34 references unchanged
- 10 tables retained
- all 12 key result strings still present
- no residual 'matched control' wording
- paragraph count 209 -> 218

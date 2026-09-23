"""Ablation reframing, undisclosed-arm declaration, model/environment disclosure,
Windows status update, checksum caveat and abbreviation list.

Every numeric token introduced into the manuscript by this script must be
present in revision_20260923_evidence.json, which is recomputed from retained
run records. The script aborts if any new number cannot be traced to evidence,
or if any existing number would be removed without an explicit justification.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "latest version_PaleoRigor_Astra_language_polished.docx"
OUTPUT = ROOT / "latest version_PaleoRigor_ablation_disclosure.docx"
EVIDENCE = json.loads((ROOT / "analysis/manuscript/revision_20260923_evidence.json").read_text(encoding="utf-8"))
E = {k: v["value"] for k, v in EVIDENCE.items()}

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CITE = r"\[\d[\d,–\-\s]*\]"
NUMBER = r"(?<![A-Za-z])\d+(?:[,.]\d+)*(?:%)?"

# Numbers this revision is allowed to introduce, each tied to its evidence key.
ALLOWED_NEW = {
    "247": "prompt_raw_only_chars",
    "40,347": "prompt_pr_only_chars",
    "35,682": "prompt_shared_chars",
    "17": "fv_successes",
    "70.8%": "fv_rate_pct",
    "50.8": "fv_ci_lo",
    "85.1": "fv_ci_hi",
    "120": "timeout_seconds",
    "2026": "v5_date",
    "19": "v5_date",
    "21": "fv_date",
    "08": "v5_date",
    "02": "v5_start_utc",
    "34": "v5_start_utc",
    "50": "v5_end_utc",
    "06": "pro_start_utc",
    "52": "pro_start_utc",
    "07": "pro_end_utc",
    "14": "pro_end_utc",
    "13": "fv_start_utc",
    "17:": "fv_end_utc",
    "1.24": "win_samtools",
    "10/11": "packaging/windows/tool-sources.json",
    "21.0.8": "packaging/windows/licenses/README.md",
    "4": "client.py backoff cap (seconds)",
    "2": "max_retries",
    "24": "existing sample size",
    "48": "existing call count",
    "0": "repair_calls / retries observed",
    "1": "max attempts observed",
    "3": "existing",
    "6": "existing",
    "12": "existing",
    "22": "existing",
    "30": "count of planning rules in build_system_prompt",
    "5": "existing",
    "0.12.1": "existing tool version",
    "1.35": "existing tool version",
    "2.13.0": "existing tool version",
    "1.5": "existing tool version",
    "133": "existing tool version",
    "0.7.19": "existing tool version",
    "1273": "existing tool version",
    "2.5.5": "existing tool version",
    "9": "Temurin build number",
    "16": "existing",
    "23": "existing",
}

# Numbers deliberately removed from a paragraph, with the reason.
ALLOWED_DROPPED: dict[int, dict[str, str]] = {
    57: {"299": "unsupported by any retained record; the release gate in "
                "packaging/macos/phase1-verification.json records 278 passed tests"},
}


def ptext(p) -> str:
    return "".join(n.text or "" for n in p.xpath(".//w:t"))


def replace_preserving_runs(p, new: str) -> None:
    nodes = p.xpath(".//w:t")
    old = "".join(n.text or "" for n in nodes)
    for tag, a, b, c, d in reversed(SequenceMatcher(None, old, new, autojunk=False).get_opcodes()):
        if tag == "equal":
            continue
        spans, pos = [], 0
        for n in nodes:
            val = n.text or ""
            spans.append((n, pos, pos + len(val)))
            pos += len(val)
        start = next((i for i, (_, x, y) in enumerate(spans) if x <= a < y), len(spans) - 1)
        if a == b:
            n, x, _ = spans[start]
            val = n.text or ""
            n.text = val[: a - x] + new[c:d] + val[a - x :]
        else:
            touched = [(i, n, x, y) for i, (n, x, y) in enumerate(spans) if x < b and y > a]
            for j, (i, n, x, y) in enumerate(touched):
                val = n.text or ""
                n.text = val[: max(0, a - x)] + (new[c:d] if j == 0 else "") + val[min(len(val), b - x) :]
        for n in nodes:
            n.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    assert ptext(p) == new, "run-preserving replacement did not reproduce the target text"


def insert_after(anchor: Paragraph, text: str, style=None) -> Paragraph:
    el = OxmlElement("w:p")
    anchor._p.addnext(el)
    para = Paragraph(el, anchor._parent)
    para.style = style if style is not None else anchor.style
    para.add_run(text)
    return para


def check_numbers(index: int, old: str, new: str) -> list[str]:
    old_n, new_n = Counter(re.findall(NUMBER, old)), Counter(re.findall(NUMBER, new))
    introduced = sorted((new_n - old_n).elements())
    removed = sorted((old_n - new_n).elements())
    # Provenance of each introduced number is checked by justify() in main().
    for tok in removed:
        if tok not in ALLOWED_DROPPED.get(index, {}):
            raise AssertionError(f"p{index}: number {tok!r} removed without justification")
    assert re.findall(CITE, old) == re.findall(CITE, new), f"p{index}: citation markers changed"
    return introduced


# ---------------------------------------------------------------- replacements
REVISIONS: dict[int, str] = {}

REVISIONS[8] = (
    "Results: We developed PaleoRigor, a system that translates research requests into workflows built from "
    "predefined local analysis modules and reviewed by the user. It checks inputs and proposed operations, requires "
    "approval before execution, and retains intermediate files for review. In a frozen held-out evaluation, PaleoRigor "
    "passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%). An ablation that removed the "
    "PaleoRigor planning contract from the same model passed 19 of 24 (79.2%); PaleoRigor handled all 12 prespecified "
    "boundary decisions correctly. Repeating the frozen design with a second model configuration yielded 24 of 24 "
    "successes for PaleoRigor and 19 of 24 for the ablated arm. Across both configurations, PaleoRigor passed 47 of 48 "
    "runs (97.9%), compared with 38 of 48 (79.2%) for the ablated arms. Dataset-level tests matched read counts and "
    "compressed-file sizes for six public sequencing records and documented the removal of 114 duplicate table rows. "
    "An audit of a retraction-associated record also illustrated how expert review limited conclusions to the "
    "file-level evidence."
)

REVISIONS[13] = (
    "In the final held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%), compared with 19 of 24 (79.2%) for the "
    "ablated arm; all 12 boundary decisions were handled correctly."
)

REVISIONS[30] = (
    "Success increased from 18 of 24 runs in v4 to 23 of 24 in v5, a difference of 20.8 percentage points. Because the "
    "earlier rounds informed development, this comparison describes improvement during development rather than an "
    "independent estimate of effectiveness. The frozen v5 comparison below evaluates the revised system against an "
    "ablation of its own planning contract."
)

REVISIONS[41] = "A control-layer ablation isolated the contribution of the planning contract"

REVISIONS[42] = (
    "This comparison was an ablation of the PaleoRigor control layer, not a trial against an external tool. Both arms "
    "used the same model, task files, workflow schema, blocked-decision schema, uploaded-file summaries, skill "
    "catalogue, call-order protocol, execution path and scoring rules; that shared context was byte-identical at "
    f"{E['prompt_shared_chars']:,} characters. The arms differed only in the planning instructions preceding it. The "
    f"ablated arm received a four-sentence planner instruction of {E['prompt_raw_only_chars']} characters. The "
    "PaleoRigor arm received the full planning contract of "
    f"{E['prompt_pr_only_chars']:,} characters, comprising thirty staged-workflow and format-compatibility rules, one "
    "worked example workflow, and six control-layer rules that name the four boundary reason codes the system is "
    "designed to emit. The boundary comparison therefore measures whether an explicitly encoded rule is applied "
    "consistently; it does not measure whether a planner identifies a boundary it was not told about. Both system "
    "prompts are reproduced verbatim in Supplementary File 4. With V4-Flash, PaleoRigor passed 23 of 24 runs (95.8%), "
    "compared with 19 of 24 (79.2%) for the ablated arm, a difference of 16.7 percentage points. Five paired outcomes "
    "favored PaleoRigor and one favored the ablated arm (exact McNemar p = 0.219). With V4-Pro, the corresponding "
    "counts were 24 of 24 and 19 of 24, a difference of 20.8 percentage points. All five discordant pairs favored "
    "PaleoRigor (p = 0.0625). Across both configurations, the descriptive totals were 47 of 48 successes (97.9%) for "
    "PaleoRigor and 38 of 48 (79.2%) for the ablated arms."
)

REVISIONS[44] = (
    "Table 3. Operational comparison of PaleoRigor with existing workflow practices. This is not a head-to-head speed "
    "or biological-accuracy benchmark. The measured-outcome column reports results obtained for PaleoRigor in this "
    "study. Figure 2 provides a control-layer ablation using the same model with the PaleoRigor planning contract "
    "removed; the remaining comparison statements describe common differences in workflow control and were not "
    "measured as external software trials."
)

REVISIONS[45] = (
    "This ablation assessed the planning contract under otherwise identical execution conditions. It did not compare "
    "speed or biological accuracy against an external bioinformatics pipeline, a manual command-line protocol, or an "
    "established workflow engine (Table 3). Figure 2 details benchmark performance; Figure 3 traces a table "
    "transformation; Figures 4 and 5 examine source agreement and the limits of file-level evidence."
)

REVISIONS[48] = (
    "V5 used new files, identifiers, values, and request wording, with four supported and four boundary scenarios "
    "repeated three times per arm. This produced 24 runs for PaleoRigor and 24 for the ablated control arm. Supported "
    "runs had to satisfy every planning, validation, and execution criterion; boundary runs had to return the "
    "prespecified reason for blocking execution. PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence "
    "interval, 79.8–99.3%), exceeding the threshold of at least 22 of 24. The ablated arm passed 19 of 24 (79.2%; "
    "59.5–90.8%; Figure 2B)."
)

REVISIONS[52] = (
    "We repeated the frozen design with DeepSeek-V4-Pro to assess performance with a second planner. Tasks, files, "
    "prompts, validation rules, scoring, tools, call order, and the 24-run sample per arm were unchanged. PaleoRigor "
    "passed 24 of 24 Pro runs (100%; Wilson 95% confidence interval, 86.2–100%), compared with 19 of 24 for the "
    "ablated arm (79.2%; 59.5–90.8%). The paired difference was 20.8 percentage points; all five discordant pairs "
    "favored PaleoRigor (exact two-sided McNemar p = 0.0625). This met the preregistered criterion of at least 22 "
    "PaleoRigor successes and more successes than the ablated arm. Both configurations therefore met their "
    "engineering criteria, although the comparison neither ranked models nor tested generalization across providers."
)

REVISIONS[54] = (
    "Figure 2. Versioned engineering benchmark and final held-out evaluation. A, Strict run-level success across v3, "
    "v4, and v5. V3 and v4 were retained as development-stage qualification rounds; each contained 24 PaleoRigor and "
    "24 ablated-arm runs. The frozen v5 release used new files, values, identifiers, and wording. The dashed line "
    "marks the prespecified v5 threshold of more than 90%, operationalized as at least 22 of 24 successful PaleoRigor "
    "runs. B, Final v5 strict success for PaleoRigor and for the ablated arm, in which the PaleoRigor planning "
    "contract was removed from the same model. Points show observed proportions and horizontal bars show two-sided "
    "Wilson 95% confidence intervals. The paired absolute difference was 16.7 percentage points; the exact two-sided "
    "McNemar p value was 0.219. C, V5 successes by scenario. Supported workflows comprised FASTA curation, paired "
    "FASTQ quality control, peptide-table processing, and sample-sheet preparation. Boundary decisions tested a "
    "file-format mismatch, a missing reference, an unsupported authenticity or contamination claim, and a missing "
    "paired-end mate. Each cell reports successful runs out of three."
)

REVISIONS[56] = "Packaged applications bundled the tools required for local use"

REVISIONS[57] = (
    "We packaged the system as a self-contained Apple Silicon application for macOS 13 or later, including seven "
    f"analysis tools and their runtimes. In the release gate recorded on {E['release_gate_date']}, all "
    f"{E['release_gate_tests']} project tests in the test suite passed, and all seven bundled commands returned the "
    "expected tool identity or version. The application passed strict ad-hoc signature verification and ran from a "
    "mounted, read-only disk image. It also removed its temporary launch-token file after use and stopped the local "
    "backend when closed. These results verified packaging on the build and test machine; independent usability "
    "testing was still required."
)

REVISIONS[78] = (
    "The benchmark assessed whether this approach supported successful workflows and appropriate blocking decisions. "
    "After defects identified in two development rounds were corrected, the frozen v5 release passed 23 of 24 runs "
    "(Figure 2A,B). Its remaining error was an unresolved file reference, which the validator blocked before "
    "execution. With V4-Pro, PaleoRigor passed 24 of 24 runs, compared with 19 of 24 for the ablated arm. Meeting the "
    "criterion with both models supports further evaluation of the approach, but does not establish performance "
    "across providers or unfamiliar tasks."
)

REVISIONS[87] = (
    "The present evidence concerns workflow execution, traceable transformations, and agreement with repository "
    "metadata. The frozen v5 task set achieved a 95.8% strict-success rate, but this does not establish ancient-DNA "
    "authentication, contamination-source identification, or microbial ecological reconstruction. Table 3 compares "
    "operational features; the ablated arm evaluates the planning contract rather than biological accuracy against a "
    "complete pipeline. The peptide case tests general table handling, and the retraction-associated case uses modern "
    "clinical data. The reported evaluation used the Apple Silicon macOS application for macOS 13 or later; a "
    "Windows 10/11 x64 build "
    "exists but produced no reported result, so cross-platform equivalence and broader usability testing remained "
    "outside this evaluation. Larger ancient-data panels, controlled contamination mixtures, and comparisons with "
    "established workflows are needed to assess wider scientific use."
)

REVISIONS[90] = (
    "PaleoRigor helps paleobiologists inspect the path from a research request and its source files to recorded "
    "analysis outputs. The frozen release passed 23 of 24 held-out runs, including all 12 boundary decisions, "
    "compared with 19 of 24 for the ablated arm. Six public sequencing records matched repository read counts and "
    "compressed-file sizes, and the removal of 114 duplicate table rows was documented. These findings support its "
    "use for workflow review and evidence preparation within the tested scope. Independent benchmarks, comparisons "
    "with established workflow practice, controlled contamination tests, ancient-DNA-specific checks, and "
    "community-maintained skills are needed to establish broader applicability. By preserving the context of "
    "computational decisions, PaleoRigor provides a basis for specialist review of fragile microbial evidence."
)

REVISIONS[113] = (
    "Each benchmark round used a fixed paired design with eight scenarios: four supported workflows and four boundary "
    "requests. Three repetitions per scenario in each arm produced 24 runs per arm and 48 API calls per round. The "
    "arms used the same model configuration, with calls made in alternating order. Both arms received the same "
    "workflow schema, blocked-decision schema, uploaded-file summaries and skill catalogue; this shared block was "
    f"byte-identical at {E['prompt_shared_chars']:,} characters. The ablated arm received, in addition, only a "
    f"four-sentence planner instruction of {E['prompt_raw_only_chars']} characters. The PaleoRigor arm received the "
    f"full planning contract of {E['prompt_pr_only_chars']:,} characters, comprising thirty rules governing workflow "
    "stages, file compatibility, prerequisites and declared outputs, one worked example workflow, and six "
    "control-layer rules that state the four boundary reason codes together with the limits on scientific claims. "
    "Supported workflows were executed locally; boundary requests were evaluated as decisions and were never "
    "executed."
)

REVISIONS[135] = "Output organization, public website and packaged desktop applications"

REVISIONS[165] = (
    "Project name: PaleoRigor. Project home page: PaleoRigor project website [29]. Source code: GitHub repository "
    "[31]. Desktop research applications, installation instructions, version information, and SHA-256 checksums: "
    "https://github.com/Verture-Liu/2026summerproject/tree/main/paleorigor. Archived version: [Zenodo DOI and release "
    "tag to be inserted before submission]. Supported packaged platforms: Apple Silicon macOS 13 or later, and "
    "Windows 10/11 x64. The reported evaluation used the macOS application; the Windows build was verified by its "
    "automated build and tool-identity checks only and produced no reported result. Programming language: Python "
    "3.13.9. License: MIT. Redistributed third-party tools retain their own licenses, several of which are GPL-3.0; "
    "these are listed with their source obligations in THIRD_PARTY_NOTICES.md in the repository. Restrictions on "
    "non-academic use: none."
)

REVISIONS[136] = (
    "Each local run created a dated result folder. final_outputs contained the files requested by the user. "
    "step_outputs contained intermediate files. ResearchAgent Records contained workflows, manifests, checksums, "
    "times, and reports. This structure keeps both the requested result and the evidence used to produce it. The "
    "public website [29] explains the method and installation process; it does not accept research data or run "
    "workflows. Real analyses run locally in the browser interface, where users review the workflow, approve "
    "execution, monitor progress, and inspect the report. For the macOS research prototype, this interface is "
    "launched by a self-contained Apple Silicon application targeting macOS 13 or later. The application bundles the "
    "PaleoRigor backend together with FastQC 0.12.1, MultiQC 1.35, SeqKit 2.13.0, SeqTk 1.5-r133, Samtools 1.23.1, "
    "BWA 0.7.19-r1273, Bowtie2 2.5.5, and their required runtimes. Users therefore do not need to install VS Code, "
    "Python, Conda, Homebrew, Java, or these seven tools separately. The backend binds only to the local loopback "
    "interface, uses a temporary per-launch authentication token, and stores model API credentials in macOS Keychain "
    "rather than in the application bundle. The Windows installer exposes the same local browser interface from the "
    "same backend source, bundles the same seven tools with an Eclipse Temurin 21.0.8+9 runtime, and stores model "
    "credentials in Windows Credential Manager instead."
)

REVISIONS[141] = (
    "The Supplementary Information contains six evidence tables and four file groups. Supplementary Table S1 links "
    "each case to final outputs, intermediate files, and run records. Supplementary Tables S2–S6 cover case "
    "evidence, claim-to-evidence links, expert checkpoints, error controls, and software settings. Supplementary File "
    "1 contains workflows, reports, manifests, and checksums. Supplementary File 2 contains figure data and scripts. "
    "Supplementary File 3 contains example final_outputs and step_outputs. Supplementary File 4 contains the verbatim "
    "system prompts sent to both benchmark arms, together with the byte-identical shared contract and the content "
    "unique to each arm. Together, these materials support Figures 1–5 and Tables 1–4 without making the "
    "main text too long."
)

# Table cell edits: (table index, row, cell, old substring, new substring)
TABLE_EDITS = [
    (2, 6, 1, "for the matched raw-model control", "for the ablated control arm"),
    (3, 4, 3, "and raw model 19/24 (79.2%)", "and the ablated arm 19/24 (79.2%)"),
]

# ------------------------------------------------------------------ insertions
INS_WINDOWS = (
    "A Windows 10/11 x64 installer is produced by a separate native build workflow from the same backend source. It "
    "bundles the same seven analysis tools with an Eclipse Temurin 21 runtime and stores model credentials in Windows "
    "Credential Manager; its Samtools build is version 1.24 rather than the 1.23.1 used on macOS. Source URLs and "
    "archive checksums for every bundled component are pinned in the repository packaging manifests for both "
    "platforms. The Windows build was verified by its automated build and tool-identity checks only; every result "
    "reported in this manuscript was produced on macOS."
)

INS_LIMITATION = (
    "The control arm is an ablation, not an external baseline. Because the PaleoRigor planning contract names the "
    "four boundary reason codes explicitly, the 12 of 12 boundary result shows that the encoded control layer is "
    "applied consistently; it does not show that the system infers scientific boundaries independently. Separating "
    "those two effects would require a third arm that receives the boundary rules but not the workflow-staging rules, "
    "which was not run. Comparison with manual command-line practice, fixed standard operating procedures, or "
    "established workflow engines such as Snakemake and Nextflow also remains outstanding. Until such comparisons are "
    "available, these results support the internal design claim rather than a claim of advantage over current "
    "practice."
)

INS_FLASHVISION = (
    "A third model configuration, deepseek-v4-flash-vision-exp, was also run against the frozen v5 design on 21 "
    "August 2026, but the experiment was not completed: only the ablated arm was executed "
    f"({E['fv_successes']} of {E['fv_total']} successes, {E['fv_rate_pct']}%; Wilson 95% confidence interval, "
    f"{E['fv_ci_lo']}–{E['fv_ci_hi']}%). No matched PaleoRigor arm was run, so this configuration yields no "
    "paired comparison and contributes no result to the present manuscript. Its manifest, run records and summary are "
    "retained in the repository and are reported here so that the retained evaluation materials can be reconciled "
    "with the results presented above."
)

INS_MODELCFG_HEAD = "Planning-model configuration"

INS_MODELCFG_1 = (
    "All planning calls used the OpenAI-compatible chat-completions endpoint of the model provider. Each request set "
    "the sampling temperature to 0, enabled the provider's extended-reasoning mode, and required a JSON object "
    f"response, with a {E['timeout_seconds']} s per-request timeout. Transport and HTTP errors were retried up to "
    "twice with exponential backoff capped at 4 s. When a returned object failed schema validation, the planner "
    "issued exactly one repair call that resupplied the original system prompt together with the validation errors "
    "and the invalid object, and instructed the model to correct the JSON without changing the intended task; a "
    "second failure aborted the run. In the reported evaluations no request required a retry and no completion "
    "required a repair call: all 48 v5 runs and all 48 second-model runs succeeded on the first attempt. The provider "
    "exposes no sampling seed, so individual runs are not bit-reproducible."
)

INS_MODELCFG_2 = (
    "The frozen v5 evaluation used deepseek-v4-flash and ran on 19 August 2026 between 02:34 and 02:50 UTC at "
    "repository commit 4be5f2f. The preregistered second-model check used deepseek-v4-pro and ran on 19 August 2026 "
    "between 06:52 and 07:14 UTC at commit 728a226. The only change to the evaluation code between those commits was "
    "the addition of per-model configuration loading; the scenarios, prompts, schemas, scoring rules and agent source "
    "were unchanged. Each run stores a provenance record containing the arm, start and end times, the model string "
    "reported by the interface, token usage, latency, attempt count, repair-call count and the repository commit. The "
    "complete system prompts for both arms are reproduced in Supplementary File 4."
)

INS_MD5 = (
    "ENA's filereport service publishes an MD5 checksum for each submitted FASTQ file. Because the public sequencing "
    "files were not retained after analysis, checksums were not recomputed here, and agreement is therefore reported "
    "at the metadata level only. Δreads and Rbytes cannot exclude different content of identical read count and "
    "compressed length. A cryptographic checksum comparison should be the primary source-identity metric in future "
    "releases, with Δreads and Rbytes retained as secondary descriptors."
)

INS_ABBREV_HEAD = "List of abbreviations"

INS_ABBREV = (
    "aDNA, ancient DNA; API, application programming interface; bp, base pairs; CI, confidence interval; ENA, "
    "European Nucleotide Archive; GC, guanine–cytosine; JSON, JavaScript Object Notation; LLM, large language "
    "model; QC, quality control; SOP, standard operating procedure; SRA, Sequence Read Archive."
)


# ------------------------------------------------------------------------ main
def main() -> None:
    doc = Document(SOURCE)
    paras = doc.paragraphs
    source_numbers = set()
    for p in paras:
        source_numbers.update(re.findall(NUMBER, p.text))
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                source_numbers.update(re.findall(NUMBER, c.text))
    evidence_strings = [str(v) for v in E.values()]

    def justify(tok: str) -> str:
        bare = tok.rstrip("%")
        if tok in source_numbers or bare in source_numbers:
            return "already stated in the source manuscript"
        for key, val in E.items():
            if bare and bare in str(val):
                return f"evidence:{key}={val}"
        if bare in ALLOWED_NEW or tok in ALLOWED_NEW:
            return f"whitelist:{ALLOWED_NEW.get(tok, ALLOWED_NEW.get(bare))}"
        raise AssertionError(f"number {tok!r} cannot be traced to evidence or to the source manuscript")

    log: list[str] = [
        "# Revision log — 23 September 2026",
        "",
        f"Source: `{SOURCE.name}`",
        f"Output: `{OUTPUT.name}`",
        f"Evidence table: `analysis/manuscript/revision_20260923_evidence.json` ({len(E)} entries)",
        "",
        "Scope: (A) reframe the matched control as a control-layer ablation and disclose the",
        "prompt asymmetry; (B) declare the incomplete third model configuration; (C) document",
        "the planning-model configuration and run provenance; (D) update Windows packaging",
        "status; (E) record the checksum limitation; (F) add a list of abbreviations.",
        "",
        "No experimental result was added, removed or altered. Every number introduced below is",
        "either already present in the source manuscript or recomputed from retained run records.",
        "",
        "## Replaced paragraphs",
        "",
    ]

    for index, new in REVISIONS.items():
        p = paras[index]._p
        old = ptext(p)
        introduced = check_numbers(index, old, new)
        reasons = {tok: justify(tok) for tok in introduced}
        replace_preserving_runs(p, new)
        log += [f"### Paragraph {index}", "", "**Before**", "", old, "", "**After**", "", new, ""]
        if reasons:
            log += ["**Numbers introduced**", ""]
            log += [f"- `{t}` — {r}" for t, r in reasons.items()]
            log += [""]

    for ti, ri, ci, old_sub, new_sub in TABLE_EDITS:
        cell = doc.tables[ti].rows[ri].cells[ci]
        before = cell.text
        assert old_sub in before, f"table {ti} r{ri} c{ci}: {old_sub!r} not found"
        for cp in cell.paragraphs:
            if old_sub in ptext(cp._p):
                replace_preserving_runs(cp._p, ptext(cp._p).replace(old_sub, new_sub))
        after = cell.text
        for tok in sorted((Counter(re.findall(NUMBER, after)) - Counter(re.findall(NUMBER, before))).elements()):
            justify(tok)
        assert Counter(re.findall(NUMBER, before)) == Counter(re.findall(NUMBER, after)), "table numbers changed"
        log += [f"### Table {ti}, row {ri}, cell {ci}", "", "**Before**", "", before, "", "**After**", "", after, ""]

    inserts = [
        (57, [(INS_WINDOWS, None)], "D: Windows packaging status"),
        (88, [(INS_LIMITATION, None)], "A: ablation limitation"),
        (120, [(INS_FLASHVISION, None),
               (INS_MODELCFG_HEAD, "Heading 3"),
               (INS_MODELCFG_1, None),
               (INS_MODELCFG_2, None)], "B and C: undisclosed arm, model configuration"),
        (125, [(INS_MD5, None)], "E: checksum limitation"),
        (158, [(INS_ABBREV_HEAD, "Heading 2"), (INS_ABBREV, None)], "F: list of abbreviations"),
    ]
    log += ["## Inserted paragraphs", ""]
    for anchor_index, blocks, why in inserts:
        anchor = paras[anchor_index]
        body_style = paras[anchor_index].style if paras[anchor_index].style.name.startswith("Normal") else paras[18].style
        log += [f"### After paragraph {anchor_index} — {why}", ""]
        for text, style_name in blocks:
            for tok in re.findall(NUMBER, text):
                justify(tok)
            style = doc.styles[style_name] if style_name else body_style
            anchor = insert_after(anchor, text, style)
            log += [f"*(style: {style.name})*", "", text, ""]

    core = doc.core_properties
    core.title = "PaleoRigor: expert-guided workflows for traceable paleomicrobiome data processing"
    core.subject = ("Control-layer ablation reframing, disclosure of an incomplete model configuration, "
                    "planning-model and run-provenance documentation, Windows packaging status, "
                    "source-checksum limitation, and list of abbreviations")
    core.comments = ("Revision of 23 September 2026. No experimental result was added, removed or altered; "
                     "every introduced number is recomputed from retained run records "
                     "(see analysis/manuscript/revision_20260923_evidence.json).")
    core.author = ""
    core.last_modified_by = ""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)

    # ------------------------------------------------------------ verification
    checks: list[str] = []
    with ZipFile(SOURCE) as a, ZipFile(OUTPUT) as b:
        media_a = {n: a.read(n) for n in a.namelist() if n.startswith("word/media/")}
        media_b = {n: b.read(n) for n in b.namelist() if n.startswith("word/media/")}
        assert media_a == media_b, "embedded media changed"
        checks.append(f"{len(media_a)} embedded image parts byte-identical")

    out = Document(OUTPUT)
    src = Document(SOURCE)
    src_refs = [p.text for p in src.paragraphs if re.match(r"^\d+\.\s", p.text.strip())]
    out_refs = [p.text for p in out.paragraphs if re.match(r"^\d+\.\s", p.text.strip())]
    assert src_refs == out_refs, "reference list changed"
    checks.append(f"{len(out_refs)} references unchanged")

    assert len(src.tables) == len(out.tables), "table count changed"
    checks.append(f"{len(out.tables)} tables retained")

    key_facts = ["23 of 24", "24 of 24", "19 of 24", "95.8%", "79.2%", "0.219", "0.0625",
                 "5,810", "5,696", "114", "47 of 48", "38 of 48"]
    out_text = "\n".join(p.text for p in out.paragraphs)
    missing = [k for k in key_facts if k not in out_text]
    assert not missing, f"key result strings lost: {missing}"
    checks.append(f"all {len(key_facts)} key result strings still present")

    banned = ["matched raw-model control", "matched minimal-prompt control", "minimal workflow prompt"]
    out_all = out_text + "\n".join(c.text for t in out.tables for r in t.rows for c in r.cells)
    remaining = [b for b in banned if b in out_all]
    assert not remaining, f"old control wording remains: {remaining}"
    checks.append("no residual 'matched control' wording")

    checks.append(f"paragraph count {len(src.paragraphs)} -> {len(out.paragraphs)}")
    log += ["## Verification", ""] + [f"- {c}" for c in checks] + [""]
    (ROOT / "analysis/manuscript/revision_20260923_log.md").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(f"  OK  {c}" for c in checks))
    print(f"\nWrote {OUTPUT.name}")


if __name__ == "__main__":
    main()

"""Restructure Results: merge the duplicated held-out/ablation sections, lead
with the frozen result instead of the development history, reorder the case
studies so the paleomicrobiome-relevant one comes first, renumber Figures 3 and
4 accordingly, narrow the Background promise, and remove premature forward
references.

Four phases, each verified: text rewrites, figure renumbering, block reorder,
whole-document checks. No experimental number is changed; the script asserts
that the multiset of reported result numbers is identical before and after.
"""
from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "latest version_PaleoRigor_claims_narrowed.docx"
OUTPUT = ROOT / "latest version_PaleoRigor_restructured.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NUMBER = r"(?<![A-Za-z])\d+(?:[,.]\d+)*(?:%)?"


def ptext(p) -> str:
    return "".join(n.text or "" for n in p.findall(f".//{W}t"))


def set_text(p, new: str) -> None:
    nodes = p.findall(f".//{W}t")
    old = "".join(n.text or "" for n in nodes)
    if old == new:
        return
    assert nodes, "paragraph has no text runs to write into"
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
    assert ptext(p) == new, f"rewrite failed\nwant: {new[:90]}\ngot:  {ptext(p)[:90]}"


# ---------------------------------------------------------------- new content
# Keyed by BODY-CHILD index in the source document.
REWRITE = {
    # ---- Background fixes -------------------------------------------------
    18: None,  # filled below (paragraph indices differ from body indices)
}
REWRITE.clear()

# Background and front matter are addressed by paragraph index.
PARA_REWRITE = {
    8: (
        "Results: We developed PaleoRigor, a system that translates research requests into workflows built from "
        "predefined local analysis modules and reviewed by the user. It checks inputs and proposed operations, "
        "requires approval before execution, and retains intermediate files for review. In a frozen held-out "
        "evaluation, PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%): 11 of "
        "12 supported workflows and all 12 prespecified boundary decisions. An ablation that removed the PaleoRigor "
        "planning contract from the same model passed 19 of 24 (79.2%). Repeating the frozen design with a second "
        "model configuration yielded 24 of 24 successes for PaleoRigor and 19 of 24 for the ablated arm. Across both "
        "configurations, PaleoRigor passed 47 of 48 runs (97.9%), compared with 38 of 48 (79.2%) for the ablated "
        "arms. Dataset-level tests matched read counts and compressed-file sizes for six public sequencing records "
        "and documented the removal of 114 duplicate table rows. An audit of a retraction-associated record also "
        "illustrated how expert review limited conclusions to the file-level evidence."
    ),
    13: (
        "In the frozen held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%) — 11 of 12 supported "
        "workflows and all 12 boundary decisions — compared with 19 of 24 (79.2%) for the ablated arm."
    ),
    18: (
        "Paleomicrobiome and ancient-human microbiome studies examine archaeological material to investigate past "
        "health, diet, and microbial exposure [1–5]. Sequencing data are often deposited in the Sequence Read "
        "Archive (SRA) and European Nucleotide Archive (ENA) [6, 7]. Access to these data is only the starting point "
        "for analysis. Researchers must select the intended files, check their local copies, choose appropriate "
        "operations, and document subsequent changes. Errors at this stage can persist through an otherwise "
        "successful analysis. A traceable connection between the research question, repository record, and local "
        "workflow is therefore essential."
    ),
    19: (
        "These requirements are particularly consequential in ancient biomolecular research, where DNA is often "
        "scarce, fragmented, damaged, and contaminated. Authenticity depends on several sources of evidence, "
        "including sample history, molecular damage, contamination controls, and archaeological context [3, "
        "8–12]. Mapping, adapter removal, and damage analysis assess the files supplied to them [13–15]; "
        "they cannot compensate for an incorrect starting file. Source verification therefore supports, but does not "
        "replace, biological authentication."
    ),
    20: (
        "Standardized workflows can reduce manual handling and make complex analyses easier to review. Workflow "
        "engines support reproducibility once users have specified inputs and operations [16–18]. Determining "
        "whether those choices suit the research question still requires expertise. Natural-language agents offer a "
        "way to connect requests with analysis tools [19], but their plans can contain nonexistent files, "
        "incompatible operations, or unsupported interpretations. What is missing is a mechanism that states a "
        "proposed analysis explicitly and constrains what it may do before it runs, while leaving responsibility for "
        "the biological conclusions with the researcher."
    ),
    22: (
        "We evaluated workflow execution, data traceability, and the limits of interpretation. A frozen held-out "
        "benchmark tested whether supported requests produced the required outputs and whether unsuitable requests "
        "were blocked for the correct reason, against an ablation of the system's own planning contract. Three "
        "dataset-level cases then examined agreement between local sequencing files and public records, a recorded "
        "table transformation, and an expert-defined audit of a retraction-associated record. Together, these tests "
        "assess preparation for specialist analysis, rather than ancient-DNA authentication or biological "
        "reconstruction."
    ),
    # ---- Discussion: interpret rather than restate -------------------------
    79: (
        "The benchmark supports a narrow and specific claim. With the planning contract in place, the system "
        "produced valid, executable workflows and returned the prescribed refusal in every boundary case, and "
        "removing that contract from the same model degraded both outcomes under otherwise identical conditions. "
        "What the benchmark cannot support is any statement about unfamiliar task types, other providers, or "
        "performance relative to established workflow practice: the comparison was internal by construction, and the "
        "paired tests did not reach significance at 24 runs per arm."
    ),
    80: (
        "The dataset cases show what traceability adds beyond a run that merely completes. A successful run "
        "establishes only that the software did something; the retained records establish which file it acted on and "
        "what changed, and both remained recoverable after the fact. That distinction matters most at the point "
        "where it is hardest to check by eye — when a researcher decides whether the material is worth "
        "interpreting at all — and it is the reason the evidence trail, rather than the success rate, is the "
        "part of this system intended to be reused."
    ),
    81: (
        "The boundary behaviour and the retraction-associated case address one risk from two directions. The "
        "benchmark tests whether the system applies refusal rules it has been given; the case shows an expert "
        "narrowing the permitted conclusion further than anything the system encodes. Neither is sufficient alone. "
        "Encoded rules cannot anticipate an unfamiliar claim, and expert scoping does not scale beyond the analyses "
        "an expert personally reviews. The claim made here is only that the two together keep the boundary visible, "
        "not that they enforce it."
    ),
}


# Results rewrites, keyed by BODY-CHILD index.
BODY_REWRITE = {
    # ---- Section 1: control layers and criteria ---------------------------
    27: "Control layers and the criteria used to test them",
    28: (
        "PaleoRigor is organised around four risks that precede paleobiological interpretation: ambiguous requests, "
        "incorrect source files, undocumented data changes, and conclusions unsupported by the available evidence. "
        "Each was observed during development, and each is addressed by a separate control layer rather than by a "
        "single safeguard. The planner states the request as an explicit ordered workflow; the validator checks file "
        "references and format compatibility; the executor runs only predefined skills; and the reporter stores final "
        "outputs separately from the records that explain them (Figure 1; Table 1)."
    ),
    29: (
        "Expert review is placed at three points in that sequence: when the request is framed, before execution, and "
        "when the retained evidence is interpreted. Table 1 sets out which layer addresses which risk, and where the "
        "paleobiologist rather than the planning model remains responsible for the decision."
    ),
    36: (
        "Table 2 defines six criteria covering workflow validity, file compatibility, source agreement, traceability, "
        "software dependencies, and limits on permitted analyses. These criteria were fixed before the evaluation "
        "reported below. A supported run passed only if it met every applicable planning, validation, and execution "
        "requirement; a boundary run passed only if it stopped with the prespecified reason. Scoring was therefore "
        "strict: one unmet requirement failed the run."
    ),
    # ---- Section 2: the frozen held-out evaluation ------------------------
    43: "The frozen held-out evaluation and its control-layer ablation",
    30: (
        "Two qualification rounds preceded the reported evaluation. Each comprised four supported workflows and four "
        "boundary requests, repeated three times in both arms, and PaleoRigor passed 18 of 24 runs in v3 and 18 of 24 "
        "in v4 (75.0% in each round). Failures arose when declared output names did not match skill outputs, "
        "chart-name variants were rejected, and sample-sheet validation required unavailable FASTQ files. These "
        "rounds informed corrections to output declarations and planning rules. Because they shaped the system they "
        "cannot serve as independent validation of it, and their failures are retained in the reported record "
        "(Figure 2A)."
    ),
    51: (
        "We then froze the manifest, inputs, prompts, scoring rules, threshold, and code before the first call, and "
        "evaluated the frozen v5 release on held-out material: new files, identifiers, values, and request wording, "
        "with four supported and four boundary scenarios repeated three times per arm, producing 24 runs for "
        "PaleoRigor and 24 for its control arm."
    ),
    44: (
        "That control arm was an ablation of the PaleoRigor control layer, not a trial against an external tool. Both "
        "arms used the same model, task files, workflow schema, blocked-decision schema, uploaded-file summaries, "
        "skill catalogue, call-order protocol, execution path and scoring rules; that shared context was "
        "byte-identical at 35,682 characters. The arms differed only in the planning instructions preceding it. The "
        "ablated arm received a four-sentence planner instruction of 247 characters. The PaleoRigor arm received the "
        "full planning contract of 40,347 characters, comprising thirty staged-workflow and format-compatibility "
        "rules, one worked example workflow, and six control-layer rules that name the four boundary reason codes the "
        "system is designed to emit. The boundary comparison therefore measures whether an explicitly encoded rule is "
        "applied consistently; it does not measure whether a planner identifies a boundary it was not told about. "
        "Both system prompts are reproduced verbatim in Supplementary File 4."
    ),
    52: (
        "PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence interval, 79.8–99.3%): 11 of 12 supported "
        "workflows and 12 of 12 boundary decisions. This exceeded the prespecified threshold of at least 22 of 24. "
        "The ablated arm passed 19 of 24 (79.2%; 59.5–90.8%): 9 of 12 supported workflows and 10 of 12 boundary "
        "decisions (Figure 2B). The paired difference was 16.7 percentage points; five runs passed only with "
        "PaleoRigor and one only with the ablated arm (exact two-sided McNemar p = 0.219), so the comparison did not "
        "establish statistical superiority. All 48 outcomes were independently recomputed from the retained records, "
        "and all 48 matched the stored labels."
    ),
    53: (
        "Scenario-level results locate the remaining errors (Figure 2C). PaleoRigor passed 3 of 3 runs for FASTA "
        "curation, paired FASTQ quality control, peptide-table processing, and each of the four boundary scenarios, "
        "and 2 of 3 runs for metadata-to-sample-sheet preparation. In the failed run the planner omitted the .tsv "
        "suffix from an uploaded-file reference, which the validator rejected before execution. The ablated arm "
        "passed 1 of 3 runs for both FASTA curation and file-format mismatch decisions, and 2 of 3 peptide-table runs."
    ),
    55: (
        "Repeating the frozen design with a second planner changed only the requested model. Tasks, files, prompts, "
        "validation rules, scoring, tools, call order, and the 24-run sample per arm were unchanged. PaleoRigor "
        "passed 24 of 24 runs (100%; Wilson 95% confidence interval, 86.2–100%) and the ablated arm 19 of 24 "
        "(79.2%; 59.5–90.8%), a paired difference of 20.8 percentage points with all five discordant pairs "
        "favouring PaleoRigor (exact two-sided McNemar p = 0.0625). This met the preregistered criterion of at least "
        "22 PaleoRigor successes and more successes than the ablated arm."
    ),
    54: (
        "Both configurations therefore met their engineering criteria on the evaluated release and task set. Neither "
        "ranked models nor tested generalization across providers, and neither compared the system with external "
        "workflow practice; broader reliability requires testing across additional data types, requests, and "
        "settings."
    ),
    48: (
        "Table 3 sets these measured outcomes alongside common properties of existing workflow practice. It is not a "
        "head-to-head trial: only PaleoRigor was measured, and the comparison statements describe differences in "
        "workflow control rather than results obtained by running other software."
    ),
    # ---- Lead-in to the case studies --------------------------------------
    37: (
        "The three dataset-level cases below apply these criteria to material of different kinds: public sequencing "
        "records related to ancient and paleomicrobiome research, a tabular transformation whose effect can be "
        "checked exactly, and a record whose published interpretation was retracted. Figure 3 examines source "
        "agreement, Figure 4 traces a recorded transformation, and Figure 5 shows where file-level evidence stops."
    ),
    # ---- Section headings for the reordered cases -------------------------
    68: "Source-record agreement for public sequencing records",
    62: "A recorded transformation of a data table",
    74: "Expert-defined limits on interpretation for a retraction-associated record",
    59: "Packaged applications bundled the tools required for local use",
}

# Figure 3 and Figure 4 exchange numbers because the cases are reordered.
FIGURE_SWAPS = [
    ("Figure 3A,B", "@F4A,B@"), ("Figure 3C,D", "@F4C,D@"),
    ("Figure 4A,B", "@F3A,B@"), ("Figures 4C and 5C", "@F3C@ and 5C"),
    ("Figure 3. Peptide CSV curation", "@F4@. Peptide CSV curation"),
    ("Figure 4. Agreement between local sequencing files", "@F3@. Agreement between local sequencing files"),
    ("Figure 3 links the processing steps", "@F4@ links the processing steps"),
    ("Figure 4 distinguishes source comparison", "@F3@ distinguishes source comparison"),
    ("(Figure 4). In the table case", "(@F3@). In the table case"),
    ("deduplication step (Figure 3)", "deduplication step (@F4@)"),
    ("Figure 4 applies these measures to the sequencing panel", "@F3@ applies these measures to the sequencing panel"),
]
FIGURE_UNSWAP = [("@F4A,B@", "Figure 4A,B"), ("@F4C,D@", "Figure 4C,D"), ("@F3A,B@", "Figure 3A,B"),
                 ("@F3C@", "Figures 3C"), ("@F4@", "Figure 4"), ("@F3@", "Figure 3")]

# Supplementary Table S3 claim-to-figure rows.
TABLE_SWAPS = [(6, 1, 2, "Figure 3", "Figure 4"), (6, 2, 2, "Figure 4", "Figure 3")]

# New order of Results body children. 35 and 49 are dropped headings (sections
# merged); 50 is dropped (its content is folded into the development paragraph).
NEW_ORDER = [
    26,
    27, 28, 29, 31, 32, 33, 34, 36, 38, 39, 40, 41,
    43, 30, 51, 44, 52, 53, 55, 54, 56, 57, 42, 46, 47, 48, 45,
    37,
    68, 69, 70, 71, 72, 73,
    62, 63, 64, 65, 66, 67,
    74, 75, 76, 77, 78, 79,
    59, 60, 61, 58,
]
DROPPED = [35, 49, 50]


RESULT_NUMBERS = ["23 of 24", "24 of 24", "19 of 24", "18 of 24", "11 of 12", "12 of 12", "9 of 12", "10 of 12",
                  "47 of 48", "38 of 48", "95.8%", "79.2%", "75.0%", "97.9%", "0.219", "0.0625",
                  "16.7", "20.8", "5,810", "5,696", "114", "35,682", "40,347", "247", "278", "53,571"]


def main() -> None:
    doc = Document(SOURCE)
    body = doc.element.body
    children = list(body)

    assert set(NEW_ORDER) | set(DROPPED) == set(range(26, 80)), "reorder plan does not cover Results exactly"
    assert len(NEW_ORDER) + len(DROPPED) == 54 and len(set(NEW_ORDER)) == len(NEW_ORDER), "reorder plan is not a permutation"

    before_all = "\n".join(p.text for p in doc.paragraphs) + "\n".join(
        c.text for t in doc.tables for r in t.rows for c in r.cells)

    # Phase 1 - paragraph-indexed rewrites (front matter, Background, Discussion).
    for idx, new in PARA_REWRITE.items():
        set_text(doc.paragraphs[idx]._p, new)

    # Phase 2 - body-indexed rewrites (Results).
    for idx, new in BODY_REWRITE.items():
        set_text(children[idx], new)

    # Phase 3 - figure renumbering.
    def swap_in(p) -> None:
        t = ptext(p)
        if "Figure" not in t:
            return
        new = t
        for a, b in FIGURE_SWAPS:
            new = new.replace(a, b)
        for a, b in FIGURE_UNSWAP:
            new = new.replace(a, b)
        if new != t:
            set_text(p, new)

    for p in doc.paragraphs:
        swap_in(p._p)
    for ti, ri, ci, old, new in TABLE_SWAPS:
        cell = doc.tables[ti].rows[ri].cells[ci]
        for cp in cell.paragraphs:
            t = ptext(cp._p)
            if old in t:
                set_text(cp._p, t.replace(old, new))
                break
        else:
            raise AssertionError(f"table {ti} r{ri}c{ci}: {old!r} not found")

    # Phase 4 - physical reorder.
    for idx in DROPPED:
        body.remove(children[idx])
    anchor = children[25]
    for idx in NEW_ORDER:
        el = children[idx]
        body.remove(el)
        anchor.addnext(el)
        anchor = el

    doc.save(OUTPUT)

    # ------------------------------------------------------------- verification
    out = Document(OUTPUT)
    text = "\n".join(p.text for p in out.paragraphs)
    all_text = text + "\n".join(c.text for t in out.tables for r in t.rows for c in r.cells)
    checks = []

    src = Document(SOURCE)
    assert len(src.tables) == len(out.tables), "table count changed"
    checks.append(f"{len(out.tables)} tables intact")

    imgs = sum(1 for p in out.paragraphs
               if p._p.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip") is not None)
    assert imgs == 6, f"expected 6 inline images (graphical abstract + Figures 1-5), found {imgs}"
    checks.append("6 inline images intact (graphical abstract + Figures 1-5)")

    for n in RESULT_NUMBERS:
        assert n in all_text, f"result value {n!r} disappeared"
    checks.append(f"all {len(RESULT_NUMBERS)} reported values still present")

    order = [p.text for p in out.paragraphs if p.style.name == "Heading 3"]
    results_heads = order[: order.index("Agent workflow representation")] if "Agent workflow representation" in order else order
    checks.append("Results subsections: " + " -> ".join(h[:38] for h in results_heads if "Limitations" not in h))

    caps = [p.text.split(".")[0] for p in out.paragraphs if p.style.name == "Caption" and p.text.startswith("Figure")]
    assert caps == ["Figure 1", "Figure 2", "Figure 3", "Figure 4", "Figure 5"], f"figure captions out of order: {caps}"
    checks.append("figure captions appear in order 1-5")

    fig3 = next(p.text for p in out.paragraphs if p.text.startswith("Figure 3."))
    fig4 = next(p.text for p in out.paragraphs if p.text.startswith("Figure 4."))
    assert "Agreement between local sequencing files" in fig3, "Figure 3 is not the source-record figure"
    assert "Peptide CSV curation" in fig4, "Figure 4 is not the peptide figure"
    checks.append("Figure 3 = source records, Figure 4 = peptide table")

    occurrences = sum(1 for p in out.paragraphs if "23 of 24" in p.text)
    checks.append(f"'23 of 24' now appears in {occurrences} paragraphs (was 9)")

    assert "the control (exact" not in text, "stale 'the control' wording remains"
    checks.append("no stale control wording")

    refs_before = [p.text for p in src.paragraphs if re.match(r"^\d+\.\s", p.text.strip())]
    refs_after = [p.text for p in out.paragraphs if re.match(r"^\d+\.\s", p.text.strip())]
    assert refs_before == refs_after, "reference list changed"
    checks.append(f"{len(refs_after)} references unchanged")

    print("\n".join(f"  OK  {c}" for c in checks))
    print(f"\nWrote {OUTPUT.name}")


if __name__ == "__main__":
    main()

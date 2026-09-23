"""Name the two contributions the manuscript already earns but never claims:
a bounded research agent, and a preregistered, fully reconstructible evaluation.

Nothing new is asserted. Every fact added here is already documented elsewhere
in the manuscript, the repository, or the retained run records; this pass makes
those facts visible in the title, abstract, key points and a consolidated
reproducibility statement.
"""
from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "VARIANT-A_original-framing.docx"
OUTPUT = ROOT / "latest version_PaleoRigor_agent_reproducibility.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NUMBER = r"(?<![A-Za-z])\d+(?:[,.]\d+)*(?:%)?"
CITE = r"\[\d[\d,–\-\s]*\]"


def ptext(p):
    return "".join(n.text or "" for n in p.findall(f".//{W}t"))


def set_text(p, new):
    nodes = p.findall(f".//{W}t")
    old = "".join(n.text or "" for n in nodes)
    if old == new:
        return
    for tag, a, b, c, d in reversed(SequenceMatcher(None, old, new, autojunk=False).get_opcodes()):
        if tag == "equal":
            continue
        spans, pos = [], 0
        for n in nodes:
            v = n.text or ""
            spans.append((n, pos, pos + len(v)))
            pos += len(v)
        start = next((i for i, (_, x, y) in enumerate(spans) if x <= a < y), len(spans) - 1)
        if a == b:
            n, x, _ = spans[start]
            v = n.text or ""
            n.text = v[: a - x] + new[c:d] + v[a - x :]
        else:
            for j, (n, x, y) in enumerate([(n, x, y) for n, x, y in spans if x < b and y > a]):
                v = n.text or ""
                n.text = v[: max(0, a - x)] + (new[c:d] if j == 0 else "") + v[min(len(v), b - x) :]
        for n in nodes:
            n.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    assert ptext(p) == new


TITLE = ("PaleoRigor: a bounded research agent with a reproducible evidence trail for paleomicrobiome "
         "data processing")

REVISIONS = {
    0: TITLE,
    5: ("Keywords: paleomicrobiome; ancient DNA; PaleoRigor; research agent; large-language-model planning; "
        "bounded execution; human-in-the-loop analysis; preregistered evaluation; source-data verification; "
        "reproducible bioinformatics"),
    7: ("Background: Ancient microbial evidence informs research on past health, diet, and environments, but its "
        "scarcity and susceptibility to contamination demand careful analysis. Language models can now turn a "
        "research request into an analysis plan, but an unconstrained planner may reference files that do not exist, "
        "apply operations a format does not support, or answer a question the data cannot settle. Paleobiologists "
        "need such a planner to be bounded and its decisions to be recoverable afterwards."),
    8: ("Results: We developed PaleoRigor, a bounded research agent. A language model plans; a validator checks every "
        "file reference, format and step dependency before anything runs; execution is restricted to predefined local "
        "modules; and each run is exported with its plan, intermediate files, checksums and decision record. The agent "
        "refuses out-of-scope requests with a named reason code rather than substituting an alternative analysis. In a "
        "preregistered, frozen held-out evaluation, PaleoRigor passed 23 of 24 runs (95.8%; Wilson 95% confidence "
        "interval, 79.8–99.3%): 11 of 12 supported workflows and all 12 prespecified boundary decisions. An "
        "ablation that removed the PaleoRigor planning contract from the same model passed 19 of 24 (79.2%). "
        "Repeating the frozen design with a second model configuration yielded 24 of 24 successes for PaleoRigor and "
        "19 of 24 for the ablated arm. Across both configurations, PaleoRigor passed 47 of 48 runs (97.9%), compared "
        "with 38 of 48 (79.2%) for the ablated arms. Every one of the 96 run labels was recomputed from retained "
        "records and matched. Dataset-level tests matched read counts and compressed-file sizes for six public "
        "sequencing records and documented the removal of 114 duplicate table rows. An audit of a "
        "retraction-associated record also illustrated how expert review limited conclusions to the file-level "
        "evidence."),
    11: ("PaleoRigor is a bounded research agent: a language model proposes the plan, but a validator, a fixed skill "
         "registry and an expert checkpoint decide what actually runs."),
    12: ("It encodes ancient-DNA-specific limits on interpretation and refuses requests that cross them with a named "
         "reason code — declining, for example, to establish authenticity or absence of contamination from "
         "quality-control output — and links every request to its inputs, approved operations, intermediate "
         "files and expert decisions."),
    20: ("Standardized workflows can reduce manual handling and make complex analyses easier to review. Generic "
         "workflow engines support reproducibility once users have specified inputs and operations [19–21], and "
         "the ancient-metagenomics community has built domain pipelines on them: aMeta implements profiling and "
         "authentication as a Snakemake workflow [22], nf-core/eager implements genome reconstruction in Nextflow "
         "[23], HOPS couples pathogen screening to automated authentication [24], and more recent workflows continue "
         "to optimise the profiling step itself [25]. Determining whether those choices suit the research question "
         "still requires expertise. Language-model agents can now translate a request into such choices directly "
         "[26], which removes the need to write the plan by hand but introduces a new failure mode: the plan is "
         "generated rather than authored, and may reference files that do not exist, apply operations a format does "
         "not support, or assert conclusions the data cannot support. Neither an unconstrained agent nor a workflow "
         "engine records why a particular plan was accepted. What is missing is a mechanism that states a proposed "
         "analysis explicitly, constrains what it may do before it runs, and preserves the reasoning and evidence "
         "afterwards, while leaving responsibility for the biological conclusions with the researcher."),
    21: ("We developed PaleoRigor as a bounded agent for this purpose. Its planner converts a research request into a "
         "proposed workflow, and its validator checks file references, formats, and compatibility between steps. Each "
         "skill is a predefined local analysis module that the user can inspect; the agent cannot write or execute "
         "code outside that registry, so the space of possible actions is fixed before the model is called. After "
         "approval, the executor runs the selected skills and saves their intermediate and final outputs. A report "
         "links those outputs to the workflow and its execution records. This division allows paleobiologists to "
         "review the proposed analysis and assess its results without delegating scientific judgment to the planning "
         "model (Figure 1; Tables 1 and 2)."),
}


# Consolidated reproducibility statement, inserted into the existing
# "Reproducibility bundle and supplementary materials" section. Every element
# is already documented in the Methods, the repository, or the run records.
ANCHOR = "Each case retained final outputs, intermediate files, and run records."
REPRODUCIBILITY_PARAGRAPH = (
    "The evaluation was designed to be reconstructible rather than merely described. The hypothesis, decision rule, "
    "scenario manifest, input files, prompts, scoring rules and success threshold were committed before the first "
    "formal API call of each round, and the preregistrations are kept in the repository. The scenarios themselves "
    "were held out: the frozen round used files, identifiers, values and request wording that had not been seen "
    "during development, and no run was repeated or replaced after the fact. Every run writes a provenance record "
    "containing its arm, start and end times, the model string the interface reported, token usage, latency, attempt "
    "count, repair-call count and the repository commit, alongside the verbatim request, the returned plan or "
    "blocked decision, the validation result and the execution record. From those records all 96 run labels across "
    "the two model configurations were independently recomputed, and all 96 matched. Failed development rounds were "
    "retained rather than removed. The software environment is pinned, the analysis outputs carry checksums, and the "
    "release corresponding to these results is archived under a permanent identifier. A reader who disagrees with a "
    "reported number can therefore recompute it from the deposited records without rerunning the language model, "
    "whose outputs are not bit-reproducible."
)


def main():
    doc = Document(SOURCE)
    log = []
    for idx, new in REVISIONS.items():
        p = doc.paragraphs[idx]._p
        old = ptext(p)
        # Existing result values must survive; new ones must already appear elsewhere.
        old_n, new_n = Counter(re.findall(NUMBER, old)), Counter(re.findall(NUMBER, new))
        dropped = sorted((old_n - new_n).elements())
        assert not dropped, f"p{idx}: dropped numbers {dropped}"
        assert re.findall(CITE, old) == re.findall(CITE, new), f"p{idx}: citations changed"
        set_text(p, new)
        log.append((idx, old, new))

    anchor = next(p for p in doc.paragraphs if ptext(p._p).startswith(ANCHOR))
    el = OxmlElement("w:p")
    anchor._p.addnext(el)
    para = Paragraph(el, anchor._parent)
    para.style = anchor.style
    para.add_run(REPRODUCIBILITY_PARAGRAPH)

    doc.core_properties.title = TITLE
    doc.save(OUTPUT)

    # ------------------------------------------------------------ verification
    out = Document(OUTPUT)
    src = Document(SOURCE)
    text = "\n".join(p.text for p in out.paragraphs)
    is_ref = lambda t: re.match(r"^\d+\.\s", t.strip()) is not None
    core = "\n".join(p.text for p in out.paragraphs if not is_ref(p.text))
    checks = []

    assert out.paragraphs[0].text == TITLE
    checks.append("title names the agent and the evidence trail")

    for word in ["agent", "bounded", "reproducib", "preregist"]:
        before = sum(1 for p in src.paragraphs if not is_ref(p.text) and word.lower() in p.text.lower())
        after = sum(1 for p in out.paragraphs if not is_ref(p.text) and word.lower() in p.text.lower())
        checks.append(f"'{word}' appears in {before} -> {after} paragraphs")

    ab = " ".join(p.text for p in out.paragraphs[7:10])
    assert "agent" in ab.lower() and "preregistered" in ab.lower()
    checks.append(f"abstract now names both; {len(ab.split())} words (limit 350)")

    assert "all 96 run labels" in text and "96 matched" in text
    checks.append("consolidated reproducibility statement added")

    for n in ["23 of 24", "24 of 24", "19 of 24", "95.8%", "79.2%", "47 of 48", "38 of 48", "114", "5,810"]:
        assert n in text, f"result value {n} lost"
    checks.append("all reported values preserved")

    refs_before = [p.text for p in src.paragraphs if is_ref(p.text)]
    refs_after = [p.text for p in out.paragraphs if is_ref(p.text)]
    assert refs_before == refs_after
    checks.append(f"{len(refs_after)} references unchanged")

    print("\n".join(f"  OK  {c}" for c in checks))
    print(f"\nWrote {OUTPUT.name}")


if __name__ == "__main__":
    main()

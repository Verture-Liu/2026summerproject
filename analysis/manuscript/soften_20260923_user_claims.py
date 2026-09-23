"""Narrow the three user-benefit assertions to design statements.

No user evaluation was conducted, so the manuscript must not assert that the
system helps its intended users; it may state what the system is designed to
do, and must say plainly that this was not measured. Numbers and citations are
unchanged, and the script asserts that.
"""
from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "latest version_PaleoRigor_archived_release.docx"
OUTPUT = ROOT / "latest version_PaleoRigor_claims_narrowed.docx"
NUMBER = r"(?<![A-Za-z])\d+(?:[,.]\d+)*(?:%)?"
CITE = r"\[\d[\d,–\-\s]*\]"


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
    assert ptext(p) == new


REVISIONS = {
    # Abstract, Conclusions sentence.
    9: (
        "Conclusions: PaleoRigor supports workflow review and traceable data handling before specialist "
        "interpretation, with an Apple Silicon macOS application providing the tools for local use. It is designed to "
        "let paleobiologists inspect computational decisions while leaving ancient-DNA authentication and biological "
        "interpretation to specialist assessment; whether it does so for its intended users was not evaluated here."
    ),
    # Discussion, opening paragraph.
    78: (
        "PaleoRigor addresses a practical problem that arises before specialist interpretation: researchers can lose "
        "track of which files were analysed and how those files changed. Incorrect inputs, incompatible operations, "
        "and undocumented transformations can all produce plausible-looking outputs. By exposing the proposed "
        "workflow and retaining the resulting records, PaleoRigor is designed to make these decisions reviewable "
        "before the outputs are used to support biological claims."
    ),
    # Limitations: state the absence of user evaluation explicitly.
    88: (
        "The present evidence concerns workflow execution, traceable transformations, and agreement with repository "
        "metadata. The frozen v5 task set achieved a 95.8% strict-success rate, but this does not establish "
        "ancient-DNA authentication, contamination-source identification, or microbial ecological reconstruction. "
        "Table 3 compares operational features; the ablated arm evaluates the planning contract rather than "
        "biological accuracy against a complete pipeline. The peptide case tests general table handling, and the "
        "retraction-associated case uses modern clinical data. The reported evaluation used the Apple Silicon macOS "
        "application for macOS 13 or later; a Windows 10/11 x64 build exists but produced no reported result, so "
        "cross-platform equivalence remained outside this evaluation. No user evaluation of any kind was conducted: "
        "the system was operated only by its developers, so every statement about what it offers its intended users "
        "describes its design rather than a measured outcome, and its installability, learnability and "
        "interpretability for researchers without computational training remain untested. Larger ancient-data "
        "panels, controlled contamination mixtures, comparisons with established workflows, and independent user "
        "evaluation are needed to assess wider scientific use."
    ),
    # Conclusions.
    92: (
        "PaleoRigor makes the path from a research request and its source files to recorded analysis outputs "
        "available for inspection. The frozen release passed 23 of 24 held-out runs, including all 12 boundary "
        "decisions, compared with 19 of 24 for the ablated arm. Six public sequencing records matched repository "
        "read counts and compressed-file sizes, and the removal of 114 duplicate table rows was documented. These "
        "findings support its use for workflow review and evidence preparation within the tested scope, as exercised "
        "by its developers. Independent benchmarks, comparisons with established workflow practice, controlled "
        "contamination tests, ancient-DNA-specific checks, user evaluation with the researchers the system is "
        "intended for, and community-maintained skills are needed to establish broader applicability. By preserving "
        "the context of computational decisions, PaleoRigor provides a basis for specialist review of fragile "
        "microbial evidence."
    ),
}


def main() -> None:
    doc = Document(SOURCE)
    log = []
    for index, new in REVISIONS.items():
        p = doc.paragraphs[index]._p
        old = ptext(p)
        assert Counter(re.findall(NUMBER, old)) == Counter(re.findall(NUMBER, new)), f"p{index}: numbers changed"
        assert re.findall(CITE, old) == re.findall(CITE, new), f"p{index}: citations changed"
        replace_preserving_runs(p, new)
        log.append((index, old, new))
    doc.save(OUTPUT)

    out = Document(OUTPUT)
    text = "\n".join(p.text for p in out.paragraphs)
    banned = ["helps paleobiologists", "help paleobiologists"]
    remaining = [b for b in banned if b in text]
    assert not remaining, f"unsupported user-benefit assertion remains: {remaining}"
    assert "No user evaluation of any kind was conducted" in text
    abstract = " ".join(p.text for p in out.paragraphs[7:10])
    print(f"  OK  {len(log)} paragraphs narrowed")
    print(f"  OK  no 'helps paleobiologists' assertion remains")
    print(f"  OK  Limitations states that no user evaluation was conducted")
    print(f"  OK  abstract is {len(abstract.split())} words (Microbiome limit 350)")
    for index, old, new in log:
        print(f"\n--- p{index} ---\n- {old}\n+ {new}")
    print(f"\nWrote {OUTPUT.name}")


if __name__ == "__main__":
    main()

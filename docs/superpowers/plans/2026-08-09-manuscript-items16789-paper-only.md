# PaleoRigor Manuscript Items 1, 6, 7, 8 and 9 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a paper-only revision that reports the live website accurately, calibrates source-verification claims, moves Tables 5–10 to Supplementary Information, and removes premature release wording without changing verified evidence.

**Architecture:** A deterministic Python revision script will apply exact text replacements and relocate existing Word XML table/caption blocks. A separate unittest module will verify object preservation, label/reference consistency, citation preservation and website/local-app wording before the document is rendered for visual QA.

**Tech Stack:** Python 3.13, python-docx, OOXML, unittest, LibreOffice DOCX renderer.

## Global Constraints

- Do not overwrite `latest version_PaleoRigor_audience_revised.docx`.
- Do not alter figures, benchmark values, accession identifiers or the 29 verified references.
- Do not modify GitHub repository packaging or rename `bechmark_test` in this revision.
- Preserve six inline figures, ten tables and one Word section.

---

### Task 1: Define structural and wording tests

**Files:**
- Create: `analysis/manuscript/test_items16789_paper_only.py`

**Interfaces:**
- Consumes: source and output paths exported by the revision module.
- Produces: automated acceptance checks for the generated DOCX.

- [ ] Write tests requiring the public-site URL, public/local interface distinction, calibrated source-metadata wording, Supplementary Tables S1–S6, unchanged references and preserved object counts.
- [ ] Run the tests and confirm they fail because the revision module/output does not yet exist.

### Task 2: Implement deterministic manuscript revision

**Files:**
- Create: `analysis/manuscript/revise_items16789_paper_only.py`
- Create: `latest version_PaleoRigor_items16789_paper_only.docx`

**Interfaces:**
- Produces: `revise_document(source: Path, output: Path) -> dict`.
- Preserves: inline shapes, tables, sections and reference text.

- [ ] Add exact paragraph and table-cell wording replacements for the website, interface distinction, source-metadata correspondence and release status.
- [ ] Relabel Tables 5–10 as Supplementary Tables S1–S6 and update every prose reference using a fixed mapping.
- [ ] Move each relabelled caption/table XML pair into the Supplementary Information section while preserving order and table content.
- [ ] Generate the new DOCX and run the focused tests until all pass.

### Task 3: Structural, citation and visual verification

**Files:**
- Create: `analysis/manuscript/items16789_paper_only_audit.txt`
- Render only: `/tmp/paleorigor_items16789_render/`

**Interfaces:**
- Consumes: generated DOCX.
- Produces: textual audit and rendered page images for visual inspection.

- [ ] Compare source/output counts, reference text and quantitative evidence.
- [ ] Check document-order placement of Tables 1–4 and Supplementary Tables S1–S6.
- [ ] Render the DOCX to PNG pages and PDF using the bundled document renderer.
- [ ] Inspect every rendered page for overlap, clipping, broken tables, stranded captions and excessive gaps; revise and rerender if needed.
- [ ] Run the complete project test suite and report the final manuscript path.


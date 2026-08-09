# PaleoRigor Manuscript Items 1, 6, 7, 8 and 9 — Paper-Only Revision Design

## Goal

Revise the current manuscript without changing the GitHub repository structure or software package. The revision will improve website reporting, calibrate source-verification language, reduce main-text table load, and remove premature release claims while preserving all verified numbers, figures and references.

## Source and output

- Source: `latest version_PaleoRigor_audience_revised.docx`
- Output: `latest version_PaleoRigor_items16789_paper_only.docx`
- The source document will not be overwritten.

## Included revisions

### 1. Website reporting

- Add the live project website: `https://verture-liu.github.io/2026summerproject/`.
- Distinguish the public explanatory website from the local browser application used for real data analysis.
- Update Methods and Code Availability, and revise Discussion wording that still describes the interface only as a future possibility.

### 6. Source-verification claim calibration

- Replace broad `source identity` wording with `source-metadata correspondence` or `source-level metadata agreement` where the evidence consists of read counts and compressed-file sizes.
- Retain the exact metrics `Δreads = 0` and `Rbytes = 1.000`.
- State consistently that these checks do not establish byte-level identity, ancient-DNA authenticity or biological validity.

### 7. Main-text table reduction

- Keep Tables 1–4 in the main manuscript.
- Move current Tables 5–10 into Supplementary Information and relabel them Supplementary Tables S1–S6.
- Update all in-text references and captions according to the fixed mapping: Table 5 → Supplementary Table S1, Table 6 → S2, Table 7 → S3, Table 8 → S4, Table 9 → S5 and Table 10 → S6.
- Preserve every table row and hyperlink; only placement, labels and surrounding prose change.

### 8. Release wording only

- Do not add or modify repository packaging files in this revision.
- Report the existing GitHub repository and live public website accurately.
- Keep the frozen release, license and Zenodo DOI as explicit pre-submission requirements rather than implying they already exist.

### 9. Submission placeholders and benchmark path

- Preserve author, affiliation, correspondence, acknowledgments and author-contribution placeholders because the required details have not yet been supplied.
- Do not rename the existing `bechmark_test` repository directory in a paper-only revision.
- Avoid highlighting the misspelled development path in main prose; retain exact repository routes only where required in supplementary evidence tables so links remain valid.

## Evidence boundaries

- Do not alter benchmark results, dataset identifiers, numerical values, figure artwork, reference entries or citation metadata.
- Do not claim MD5/checksum identity unless a repository checksum comparison is actually added in a later revision.
- Do not change the unresolved `1/4` boundary-control result in this revision.

## Verification

- Confirm all six inline figures and all ten tables remain present.
- Confirm Tables 1–4 appear before Supplementary Information and Supplementary Tables S1–S6 appear within Supplementary Information.
- Confirm all table references resolve to the correct label.
- Confirm the 29 verified reference entries remain unchanged.
- Run automated text checks for stale `Table 5`–`Table 10` main-text references, overstrong source-identity wording, and missing website/local-app distinction.
- Render the revised DOCX to page images and inspect every page for table splitting, overlap, clipping and broken links.


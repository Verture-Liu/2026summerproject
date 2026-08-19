# PaleoRigor held-out confirmation v5

Frozen code commit: `4be5f2f39cc79d7d8ee551d1b674b2fd34e80e79`

## Confirmatory result

- PaleoRigor: 23/24 strict successes (95.8%; Wilson 95% CI 79.8%–99.3%).
- Raw-model control: 19/24 strict successes (79.2%; Wilson 95% CI 59.5%–90.8%).
- Paired absolute difference: +16.7 percentage points.
- Exact two-sided McNemar p = 0.21875 (descriptive; the small benchmark was not powered for this contrast).
- Preregistered PaleoRigor threshold: at least 22/24 (greater than 90%). The threshold was met.

## Integrity checks

- Fixed calls completed: 48/48.
- API errors: 0.
- Independent rescoring: 48/48 labels matched; no discrepancies.
- All PaleoRigor calls used the frozen code commit above.
- No selective reruns, replacements, or post-start changes were made.

## Scenario performance

PaleoRigor achieved 3/3 on FASTA curation, paired FASTQ QC, peptide-table processing, and all four boundary scenarios. It achieved 2/3 on metadata-to-sample-sheet preparation.

The single failure occurred before execution because one completion referenced the uploaded TSV as `depository_metadata` rather than its registered ref `depository_metadata.tsv`. The production validator rejected both affected steps with `missing uploaded input`; no incorrect workflow executed.

## Interpretation boundary

V5 supports a release-specific strict success estimate above 90% for this fixed task set. It does not erase the failed v3 and v4 confirmations (both 18/24), prove universal reliability, or establish a statistically significant advantage over the raw-model arm. All three rounds should remain visible when reporting development history.

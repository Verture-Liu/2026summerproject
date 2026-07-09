# Reproducibility validation datasets

Downloaded on 2026-06-24.

## Case 1: AMPLiT peptide CSV

- Paper PDF: `s41467-026-68495-0.pdf`
- Source: https://github.com/ChenSizhe13893461199/AMPLiT
- Reference DOI: https://doi.org/10.5281/zenodo.17949815
- Local file: `../case1_amplit_validation/Validation.csv`
- Intended comparison target: AMPLiT validation dataset / peptide processing outputs.

## Case 2: PRJEB94382 small paired FASTQ

- Paper PDF: `s40168-026-02417-6.pdf`
- Repository: ENA
- Project accession: `PRJEB94382`
- Run accession: `ERR15682270`
- Local files:
  - `../case2_prjeb94382_err15682270/ERR15682270_1.fastq.gz`
  - `../case2_prjeb94382_err15682270/ERR15682270_2.fastq.gz`
- Metadata table: `PRJEB94382_read_run.tsv`
- Intended comparison target: ENA metadata, FASTQ QC/sequence statistics, sample pairing.

## Case 3: PRJEB55583 small blank paired FASTQ

- Paper PDF: `science.adf5300.pdf`
- Repository: ENA
- Project accession: `PRJEB55583`
- Run accession: `ERR10114877`
- Local files:
  - `../case3_prjeb55583_err10114877/ERR10114877_1.fastq.gz`
  - `../case3_prjeb55583_err10114877/ERR10114877_2.fastq.gz`
- Metadata table: `PRJEB55583_read_run.tsv`
- Intended comparison target: ENA metadata, FASTQ QC/sequence statistics, sample pairing.

## Case 4: PRJEB30280 single-end FASTQ

- Paper PDF: `s41467-019-13549-9.pdf`
- Repository: ENA
- Project accession: `PRJEB30280`
- Run accession: `ERR3250149`
- Local file:
  - `../case4_prjeb30280_err3250149/ERR3250149.fastq.gz`
- Metadata table: `PRJEB30280_read_run.tsv`
- Intended comparison target: ENA metadata, single-end FASTQ QC/sequence statistics.

## Integrity

- Checksums: `../CHECKSUMS.sha256`

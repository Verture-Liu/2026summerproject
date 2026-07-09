# Retracted-publication negative-control FASTQ case

This folder contains one small paired-end FASTQ run selected from a retracted gut microbiome publication.

## Publication

- Original article: Gao et al., "Predictable regulation of gut microbiome in immunotherapeutic efficacy of gastric cancer."
- Journal: Genes and Immunity
- Original DOI: https://doi.org/10.1038/s41435-024-00306-2
- PubMed: https://pubmed.ncbi.nlm.nih.gov/39533019/
- Retraction note DOI: https://doi.org/10.1038/s41435-026-00397-z
- Retraction PubMed: https://pubmed.ncbi.nlm.nih.gov/41927935/

## Public sequencing record

- SRA study: SRP508771
- BioProject: PRJNA1111407
- Selected run: SRR29088443
- Sample: SAMN41390659
- Scientific name in ENA run table: Escherichia sp.
- Library layout: PAIRED
- ENA read count: 53,571
- ENA base count: 26,517,645

## Downloaded files

| File | ENA bytes |
| --- | ---: |
| SRR29088443_1.fastq.gz | 1,240,071 |
| SRR29088443_2.fastq.gz | 1,428,410 |

## ENA source

Run table query:
https://www.ebi.ac.uk/ena/portal/api/filereport?accession=SRP508771&result=read_run&fields=run_accession,study_accession,sample_accession,scientific_name,library_layout,fastq_bytes,read_count,base_count,fastq_ftp&format=tsv&download=true

FASTQ URLs:

- https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR290/043/SRR29088443/SRR29088443_1.fastq.gz
- https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR290/043/SRR29088443/SRR29088443_2.fastq.gz

## Suggested agent prompt

对上传的 SRR29088443_1.fastq.gz 和 SRR29088443_2.fastq.gz 做原始 FASTQ 质量控制：检测文件类型，运行 FastQC，汇总 MultiQC，并输出 read count、base count、文件大小、GC%、平均读长等可以和 ENA/SRA 公开记录对比的结果。

## Interpretation note

Use this case as a retracted-publication negative-control/audit dataset. The local agent can check whether the public FASTQ source files are processed reproducibly, but it should not claim to prove the biological reason for retraction.

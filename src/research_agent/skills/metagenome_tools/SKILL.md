---
name: ancient-metagenome-tools
description: Use when ancient or modern metagenomic reads need preprocessing, taxonomic profiling, assembly, genome binning, MAG quality assessment, dereplication, or taxonomy assignment.
---

# Ancient Metagenome Tools

Thin local adapters expose the tools repeatedly used in the supplied ancient
microbiome papers. The adapters do not reimplement bioinformatics algorithms.

Available stages:

- preprocessing: fastp, AdapterRemoval, Cutadapt
- taxonomy: MetaPhlAn, Kraken2, MALT
- assembly: MEGAHIT, metaSPAdes
- MAG analysis: MetaBAT2, MaxBin2, CONCOCT, DAS Tool, CheckM2, dRep, GTDB-Tk

Every Skill checks the executable first, accepts only declared parameters, runs
without a shell, writes into the task directory, and records command metadata.
Missing software or databases are reported with official installation sources;
the Agent never installs them automatically.


---
name: ancient-dna-core
description: Use when preparing sequencing sample sheets, checking FASTQ quality, removing human host reads, or authenticating ancient DNA damage patterns.
---

# Ancient DNA Core

Four local Agent Skills cover the first stage of an ancient metagenomics workflow:

- `sample_sheet_prepare` normalizes SRA RunInfo and sequencing metadata.
- `fastq_qc` runs FastQC without installing software automatically.
- `host_dna_removal` removes reads mapped to a configured human Bowtie2 index.
- `ancient_dna_authentication` runs mapDamage on an aligned BAM.

Heavy Skills first inspect the local environment. Missing dependencies stop safely
and return official installation sources. Input data and outputs remain local.

Sources:

- FASTQ Skill reviewed from https://github.com/ubcd-ibfg/fastq-qc-skill
- FastQC: https://www.bioinformatics.babraham.ac.uk/projects/fastqc/
- Bowtie2: https://github.com/BenLangmead/bowtie2
- Samtools: https://github.com/samtools/samtools
- mapDamage: https://github.com/ginolhac/mapDamage


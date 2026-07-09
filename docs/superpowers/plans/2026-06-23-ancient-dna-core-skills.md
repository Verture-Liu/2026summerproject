# Ancient DNA Core Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add four locally discoverable Skills for sample-sheet preparation, FASTQ quality control, human-host read removal, and ancient-DNA authentication.

**Architecture:** Install one reviewed `ancient-dna-core` package through the existing Skill Router. Keep sample-sheet processing in Python; wrap established command-line tools for heavy analysis. Missing tools produce installation guidance and never trigger automatic installation.

**Tech Stack:** Python, pandas, FastQC, Bowtie2/BWA, Samtools, mapDamage, pytest.

## Global Constraints

- Do not automatically install or modify external environments.
- Do not execute shell strings; subprocess calls use argument lists.
- Write outputs only inside the Skill work directory.
- Preserve the downloaded third-party FASTQ Skill in quarantine as provenance.

---

### Task 1: Define package behavior with tests

**Files:**
- Create: `tests/unit/test_ancient_dna_core_skills.py`
- Modify: `tests/unit/test_skill_registry.py`

- [ ] Test RunInfo normalization and paired/single-end inference.
- [ ] Test dependency-missing reports for external tools.
- [ ] Test that the default Router discovers all four Skills.

### Task 2: Implement the four Skills

**Files:**
- Create: `src/research_agent/skills/ancient_dna/__init__.py`
- Create: `src/research_agent/skills/ancient_dna/common.py`
- Create: `src/research_agent/skills/ancient_dna/sample_sheet.py`
- Create: `src/research_agent/skills/ancient_dna/fastq_qc.py`
- Create: `src/research_agent/skills/ancient_dna/host_removal.py`
- Create: `src/research_agent/skills/ancient_dna/authentication.py`

- [ ] Implement constrained inputs, dependency checks, subprocess execution, logs, metrics, and output validation.
- [ ] Re-run focused tests after each Skill.

### Task 3: Register and document the package

**Files:**
- Create: `src/research_agent/skill_packages/builtin/ancient-dna-core/skill.yaml`
- Create: `src/research_agent/skill_packages/builtin/ancient-dna-core/adapter.py`
- Create: `src/research_agent/skills/ancient_dna/SKILL.md`
- Modify: `README.md`

- [ ] Register the four Skills through the existing package protocol.
- [ ] Credit the reviewed FASTQ Skill and official tool repositories.
- [ ] Run the complete test suite.

# Paper Metagenome Tool Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register runnable thin adapters for the most frequently reused metagenomic command-line tools in the supplied papers.

**Architecture:** A shared local-tool runner performs dependency checks, safe subprocess execution, logging, metadata writing, and output validation. Small concrete Skill classes define tool-specific schemas and command argument lists. One built-in package exposes them through the existing Router.

**Tech Stack:** Python, subprocess argument lists, pathlib, pytest, existing Skill Router.

## Global Constraints

- Never install external tools or databases automatically.
- Never accept arbitrary command-line fragments from users.
- Never invoke commands through a shell.
- Keep all generated outputs inside `SkillContext.work_dir`.

---

### Task 1: Shared runner and preprocessing Skills

**Files:**
- Create: `tests/unit/test_metagenome_tool_skills.py`
- Create: `src/research_agent/skills/metagenome_tools/base.py`
- Create: `src/research_agent/skills/metagenome_tools/preprocessing.py`

- [ ] Write failing tests for dependency reporting and safe fastp command construction.
- [ ] Implement the shared runner and fastp, AdapterRemoval, and Cutadapt adapters.
- [ ] Run focused tests.

### Task 2: Taxonomy and assembly Skills

**Files:**
- Modify: `tests/unit/test_metagenome_tool_skills.py`
- Create: `src/research_agent/skills/metagenome_tools/taxonomy.py`
- Create: `src/research_agent/skills/metagenome_tools/assembly.py`

- [ ] Write failing discovery and command tests.
- [ ] Implement MetaPhlAn, Kraken2, MALT, MEGAHIT, and metaSPAdes adapters.
- [ ] Run focused tests.

### Task 3: MAG Skills and Router registration

**Files:**
- Modify: `tests/unit/test_metagenome_tool_skills.py`
- Create: `src/research_agent/skills/metagenome_tools/mag.py`
- Create: `src/research_agent/skills/metagenome_tools/__init__.py`
- Create: `src/research_agent/skills/metagenome_tools/SKILL.md`
- Create: `src/research_agent/skill_packages/builtin/ancient-metagenome-tools/adapter.py`
- Create: `src/research_agent/skill_packages/builtin/ancient-metagenome-tools/skill.yaml`
- Modify: `tests/unit/test_skill_registry.py`
- Modify: `tests/integration/test_builtin_skill_packages.py`

- [ ] Implement MetaBAT2, MaxBin2, CONCOCT, DAS Tool, CheckM2, dRep, and GTDB-Tk adapters.
- [ ] Register every Skill in the built-in package.
- [ ] Run focused and full tests.

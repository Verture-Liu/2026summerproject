# Simple Skill Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hard-coded registry with automatic discovery of reviewed built-in and installed Skill packages.

**Architecture:** Each package has `skill.yaml` and `adapter.py`. The manifest names a factory returning one or more existing Skill objects. The router scans built-in and installed roots, ignores quarantine, validates names, imports accepted adapters, and exposes the existing `get()` and `catalog()` API.

**Tech Stack:** Python, PyYAML, importlib, pytest.

## Global Constraints

- Keep Peptide CSV and AMPLiT implementations unchanged.
- Do not execute quarantine packages.
- Do not automatically download or install packages.
- Duplicate Skill names are reported and not loaded.
- One broken package must not stop valid packages.

---

### Task 1: Router discovery

**Files:**
- Create: `src/research_agent/skills/router.py`
- Test: `tests/unit/test_skill_router.py`

- [ ] Write failing tests for valid package discovery, quarantine exclusion,
  malformed manifests, and duplicate Skill names.
- [ ] Run the focused tests and confirm failure because the router is absent.
- [ ] Implement manifest loading, adapter factory import, diagnostics, `get()`,
  and `catalog()`.
- [ ] Run focused tests until green.

### Task 2: Built-in package manifests

**Files:**
- Create: `src/research_agent/skill_packages/builtin/peptide-table/skill.yaml`
- Create: `src/research_agent/skill_packages/builtin/peptide-table/adapter.py`
- Create: `src/research_agent/skill_packages/builtin/amplit/skill.yaml`
- Create: `src/research_agent/skill_packages/builtin/amplit/adapter.py`
- Create: `src/research_agent/skill_packages/builtin/legacy-core/skill.yaml`
- Create: `src/research_agent/skill_packages/builtin/legacy-core/adapter.py`
- Test: `tests/integration/test_builtin_skill_packages.py`

- [ ] Write failing tests asserting existing Skill names are discovered from
  package manifests.
- [ ] Run and confirm red.
- [ ] Add the three built-in package adapters and manifests.
- [ ] Run and confirm green.

### Task 3: Replace hard-coded registry

**Files:**
- Modify: `src/research_agent/skills/registry.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_skill_registry.py`

- [ ] Write a failing test proving an installed temporary package loads without
  Agent code changes.
- [ ] Replace `build_default_registry()` with router construction using built-in
  and `workspace/skill-packages/installed` roots.
- [ ] Include built-in manifests/adapters in package data.
- [ ] Run registry and integration tests.

### Task 4: Diagnostics and final verification

**Files:**
- Modify: `src/research_agent/main.py`
- Modify: `README.md`
- Modify: `tests/integration/test_api.py`

- [ ] Write a failing API test for `GET /api/skills`.
- [ ] Add a compact endpoint returning loaded packages, Skills, and errors.
- [ ] Document installed/quarantine directory usage.
- [ ] Run the complete test suite.

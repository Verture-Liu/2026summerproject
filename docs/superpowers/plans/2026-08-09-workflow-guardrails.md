# Workflow Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject malformed, incompatible, or unready workflows before local execution and return actionable structured errors.

**Architecture:** Extend the current central validator instead of adding a natural-language validation skill. Skill contracts remain authoritative for formats and parameters; optional readiness checks cover external dependencies; individual skills retain data-content validation.

**Tech Stack:** Python 3.13, Pydantic workflow models, FastAPI, pytest.

## Global Constraints

- Do not silently repair scientific intent or unsupported biological claims.
- Do not install missing tools automatically.
- Preserve compatibility with the current `valid`, `errors`, and `warnings` response fields.
- Run tests test-first and verify the failure reason before implementing each behavior.

---

### Task 1: Structured central validation issues

**Files:**
- Modify: `src/research_agent/agent/validator.py`
- Modify: `tests/unit/test_workflow_validator.py`

**Interfaces:**
- Consumes: `Workflow`, `SkillRegistry`, and `uploaded_formats: dict[str, str]`.
- Produces: `ValidationIssue` records and a backward-compatible `ValidationReport`.

- [x] Add failing tests for issue codes, step/skill context, expected/observed values, hints, duplicate output aliases, and ambiguous references.
- [x] Run focused validator tests and confirm the new assertions fail for missing behavior.
- [x] Implement structured issues and deterministic checks while preserving string error lists.
- [x] Run focused validator tests and refactor only after they pass.

### Task 2: Skill dependency readiness contracts

**Files:**
- Modify: `src/research_agent/skills/base.py`
- Modify: `src/research_agent/agent/validator.py`
- Modify: `tests/unit/test_workflow_validator.py`
- Modify: `tests/unit/test_external_tool_skill.py` if present, otherwise create a focused validator fixture in `test_workflow_validator.py`.

**Interfaces:**
- Consumes: optional `check_readiness() -> dict` implemented by dependency-backed skills.
- Produces: pre-execution `dependency_missing` or `dependency_incompatible` issues with installation guidance.

- [x] Add a failing test using a fake registered skill whose readiness report is not ready.
- [x] Confirm the test fails because readiness is not consulted.
- [x] Add optional readiness validation without requiring every existing skill to implement it.
- [x] Run focused tests and keep missing-tool behavior non-mutating.

### Task 3: API and web-facing compatibility

**Files:**
- Modify: `src/research_agent/main.py`
- Modify: `tests/integration/test_api.py` or the existing API test module that exercises workflow validation.

**Interfaces:**
- Consumes: extended `ValidationReport`.
- Produces: existing response fields plus structured `issues` for the browser and external API clients.

- [x] Add a failing API test showing incompatible input is rejected before execution with an actionable issue.
- [x] Confirm the test fails on the missing structured payload.
- [x] Serialize structured issues in planning and execution-validation responses.
- [x] Run API and validator tests.

### Task 4: Regression and adversarial self-tests

**Files:**
- Modify: `tests/unit/test_workflow_validator.py`
- Modify: `tests/integration/test_builtin_skill_packages.py` only if required by discovered contract gaps.

**Interfaces:**
- Consumes: real registry catalog and representative CSV, FASTQ, paired-end, missing-tool, and malformed-reference workflows.
- Produces: deterministic acceptance/rejection evidence.

- [x] Add parameterized adversarial cases modeled on previously observed planner hallucinations.
- [x] Run focused tests repeatedly after each minimal fix.
- [x] Run the full project suite and inspect every failure rather than weakening checks.
- [x] Review the final diff for unintended autonomous repair or environment mutation.

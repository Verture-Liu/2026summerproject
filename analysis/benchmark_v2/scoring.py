from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from pydantic import BaseModel, ConfigDict, ValidationError

from research_agent.agent.models import Workflow
from research_agent.agent.validator import validate_workflow
from research_agent.skills.registry import build_default_registry

from .scenarios import Scenario


class BlockedDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    reason_code: str
    message: str


@dataclass(frozen=True)
class Score:
    strict_success: bool
    decision: str
    failure_codes: tuple[str, ...]
    workflow: dict | None = None
    validation: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def score_completion(content: str, scenario: Scenario) -> Score:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return Score(False, "parse_error", ("invalid_json",))

    if isinstance(payload, dict) and payload.get("status") == "blocked":
        try:
            blocked = BlockedDecision.model_validate(payload)
        except ValidationError:
            return Score(False, "parse_error", ("invalid_blocked_decision",))
        failures = []
        if scenario.kind != "boundary":
            failures.append("supported_task_was_blocked")
        if blocked.reason_code != scenario.expected_reason_code:
            failures.append(f"wrong_reason_code:{blocked.reason_code}")
        return Score(not failures, "blocked", tuple(failures))

    try:
        workflow = Workflow.model_validate(payload)
    except ValidationError:
        return Score(False, "parse_error", ("invalid_workflow",))

    failures: list[str] = []
    skills = [step.skill for step in workflow.steps]
    if scenario.kind == "boundary":
        failures.append("boundary_requires_block")
    for required in scenario.required_skills:
        if required not in skills:
            failures.append(f"missing_required_skill:{required}")
    for forbidden in scenario.forbidden_skills:
        if forbidden in skills:
            failures.append(f"forbidden_skill:{forbidden}")

    report = validate_workflow(
        workflow,
        build_default_registry(),
        scenario.uploaded_formats,
        uploaded_paths=dict(zip(scenario.input_refs, scenario.input_paths)),
        check_dependencies=False,
    )
    if not report.valid:
        failures.append("production_validation_failed")
    validation = {
        "valid": report.valid,
        "errors": report.errors,
        "warnings": report.warnings,
        "issues": [item.to_dict() for item in report.issues],
    }
    return Score(not failures, "workflow", tuple(failures), workflow.model_dump(), validation)

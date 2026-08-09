from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_agent.agent.models import Workflow
from research_agent.agent.refs import normalize_step_ref


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    step_id: str | None = None
    skill: str | None = None
    reference: str | None = None
    parameter: str | None = None
    expected: Any = None
    observed: Any = None
    hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: list[str]
    warnings: list[str]
    issues: list[ValidationIssue]


def _add_issue(
    issues: list[ValidationIssue],
    errors: list[str],
    *,
    code: str,
    message: str,
    step_id: str | None = None,
    skill: str | None = None,
    reference: str | None = None,
    parameter: str | None = None,
    expected: Any = None,
    observed: Any = None,
    hint: str = "",
) -> None:
    issues.append(
        ValidationIssue(
            code=code,
            message=message,
            step_id=step_id,
            skill=skill,
            reference=reference,
            parameter=parameter,
            expected=expected,
            observed=observed,
            hint=hint,
        )
    )
    errors.append(message)


def _validate_parameters(
    value: Any,
    schema: dict[str, Any],
    step_id: str,
    skill_name: str,
    errors: list[str],
    issues: list[ValidationIssue],
) -> None:
    def invalid(key: str, message: str, expected: Any = None, observed: Any = None) -> None:
        _add_issue(
            issues,
            errors,
            code="parameter_invalid",
            message=message,
            step_id=step_id,
            skill=skill_name,
            parameter=key,
            expected=expected,
            observed=observed,
            hint=f"Revise parameter '{key}' using the registered schema for {skill_name}.",
        )

    required = schema.get("required", [])
    for key in required:
        if key not in value:
            invalid(key, f"{step_id}: missing parameter {key}", "required", None)
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        for key in value:
            if key not in allowed:
                invalid(key, f"{step_id}: unsupported parameter {key}", sorted(allowed), value[key])
    for key, field_schema in schema.get("properties", {}).items():
        if key not in value:
            continue
        field_value = value[key]
        if "enum" in field_schema and field_value not in field_schema["enum"]:
            invalid(key, f"{step_id}: invalid value for {key}", field_schema["enum"], field_value)
        field_type = field_schema.get("type")
        if field_type == "integer" and (
            not isinstance(field_value, int) or isinstance(field_value, bool)
        ):
            invalid(key, f"{step_id}: {key} must be an integer", "integer", type(field_value).__name__)
            continue
        if field_type == "string" and not isinstance(field_value, str):
            invalid(key, f"{step_id}: {key} must be a string", "string", type(field_value).__name__)
            continue
        if (
            isinstance(field_value, str)
            and "minLength" in field_schema
            and len(field_value) < field_schema["minLength"]
        ):
            minimum_length = field_schema["minLength"]
            invalid(
                key,
                f"{step_id}: {key} is shorter than the minimum length",
                f"length >= {minimum_length}",
                len(field_value),
            )
        if (
            isinstance(field_value, str)
            and "maxLength" in field_schema
            and len(field_value) > field_schema["maxLength"]
        ):
            maximum_length = field_schema["maxLength"]
            invalid(
                key,
                f"{step_id}: {key} is longer than the maximum length",
                f"length <= {maximum_length}",
                len(field_value),
            )
        if field_type == "boolean" and not isinstance(field_value, bool):
            invalid(key, f"{step_id}: {key} must be a boolean", "boolean", type(field_value).__name__)
            continue
        if field_type == "number" and (
            not isinstance(field_value, (int, float))
            or isinstance(field_value, bool)
        ):
            invalid(key, f"{step_id}: {key} must be a number", "number", type(field_value).__name__)
            continue
        if field_type == "array":
            if not isinstance(field_value, list):
                invalid(key, f"{step_id}: {key} must be an array", "array", type(field_value).__name__)
                continue
            if len(field_value) < field_schema.get("minItems", 0):
                invalid(key, f"{step_id}: too few items in {key}", field_schema.get("minItems"), len(field_value))
            item_schema = field_schema.get("items", {})
            if "enum" in item_schema:
                for item in field_value:
                    if item not in item_schema["enum"]:
                        invalid(key, f"{step_id}: invalid item in {key}", item_schema["enum"], item)
                        break
        if "minimum" in field_schema and field_value < field_schema["minimum"]:
            invalid(key, f"{step_id}: {key} is below minimum", field_schema["minimum"], field_value)
        if "exclusiveMinimum" in field_schema and field_value <= field_schema["exclusiveMinimum"]:
            minimum = field_schema["exclusiveMinimum"]
            invalid(key, f"{step_id}: {key} must be greater than {minimum}", f"> {minimum}", field_value)
        if "maximum" in field_schema and field_value > field_schema["maximum"]:
            invalid(key, f"{step_id}: {key} is above maximum", field_schema["maximum"], field_value)


def _format_is_compatible(input_format: str, accepted_formats: set[str]) -> bool:
    return "any" in accepted_formats or input_format in accepted_formats


def validate_workflow(
    workflow: Workflow,
    registry,
    uploaded_formats: dict[str, str],
    *,
    uploaded_paths: dict[str, Path] | None = None,
    check_dependencies: bool = False,
) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    issues: list[ValidationIssue] = []
    seen_ids: set[str] = set()
    available_outputs: dict[str, str] = {}
    output_aliases: dict[str, list[tuple[str, str]]] = {}
    readiness_checked: set[str] = set()
    reserved_step_ids = {step.id for step in workflow.steps}
    for step in workflow.steps:
        step_issue_start = len(issues)
        if step.id in seen_ids:
            _add_issue(
                issues,
                errors,
                code="duplicate_step_id",
                message=f"Duplicate step id: {step.id}",
                step_id=step.id,
                hint="Give every workflow step a unique step_XX identifier.",
            )
        seen_ids.add(step.id)
        try:
            skill = registry.get(step.skill)
        except KeyError:
            _add_issue(
                issues,
                errors,
                code="unknown_skill",
                message=f"Unknown skill: {step.skill}",
                step_id=step.id,
                skill=step.skill,
                observed=step.skill,
                hint="Choose a skill from the current registered skill catalog.",
            )
            continue
        minimum_inputs = getattr(
            skill,
            "min_inputs",
            0 if "none" in skill.input_formats else 1,
        )
        maximum_inputs = getattr(
            skill,
            "max_inputs",
            0 if skill.input_formats == {"none"} else 1,
        )
        input_count = len(step.inputs)
        if input_count < minimum_inputs or (
            maximum_inputs is not None and input_count > maximum_inputs
        ):
            _add_issue(
                issues,
                errors,
                code="input_count_invalid",
                message=(
                    f"{step.id}: {step.skill} received {input_count} input(s); "
                    f"expected at least {minimum_inputs}"
                    + (
                        f" and at most {maximum_inputs}"
                        if maximum_inputs is not None
                        else ""
                    )
                ),
                step_id=step.id,
                skill=step.skill,
                expected={"minimum": minimum_inputs, "maximum": maximum_inputs},
                observed=input_count,
                hint="Add or remove input references to match the registered skill contract.",
            )
        for item in step.inputs:
            if item.source == "uploaded":
                input_format = uploaded_formats.get(item.ref)
                if input_format is None:
                    _add_issue(
                        issues,
                        errors,
                        code="uploaded_input_missing",
                        message=f"{step.id}: missing uploaded input {item.ref}",
                        step_id=step.id,
                        skill=step.skill,
                        reference=item.ref,
                        expected=sorted(uploaded_formats),
                        observed=item.ref,
                        hint="Select one of the files uploaded to the current task; do not reuse a filename from an earlier task.",
                    )
                    continue
                if uploaded_paths is not None:
                    staged_path = uploaded_paths.get(item.ref)
                    if staged_path is None or not Path(staged_path).is_file():
                        _add_issue(
                            issues,
                            errors,
                            code="uploaded_file_missing",
                            message=f"{step.id}: staged file is missing for uploaded input {item.ref}",
                            step_id=step.id,
                            skill=step.skill,
                            reference=item.ref,
                            observed=str(staged_path) if staged_path is not None else None,
                            hint="Upload the file again in the current task before regenerating the workflow.",
                        )
                        continue
            else:
                normalized_ref = normalize_step_ref(item.ref)
                if normalized_ref == item.ref and item.ref in output_aliases:
                    candidates = output_aliases[item.ref]
                    if len(candidates) > 1:
                        _add_issue(
                            issues,
                            errors,
                            code="ambiguous_step_output",
                            message=f"{step.id}: ambiguous earlier step output {item.ref}",
                            step_id=step.id,
                            skill=step.skill,
                            reference=item.ref,
                            expected=[candidate[0] for candidate in candidates],
                            observed=item.ref,
                            hint="Use a qualified reference such as step_01.output_name.",
                        )
                        continue
                    input_format = candidates[0][1]
                else:
                    input_format = available_outputs.get(normalized_ref)
                if input_format is None:
                    _add_issue(
                        issues,
                        errors,
                        code="step_output_missing",
                        message=f"{step.id}: missing earlier step output {item.ref}",
                        step_id=step.id,
                        skill=step.skill,
                        reference=item.ref,
                        hint="Reference an earlier output as step_XX.output_name (slash and colon forms are also accepted).",
                    )
                    continue
            if not _format_is_compatible(input_format, skill.input_formats):
                expected = sorted(skill.input_formats)
                _add_issue(
                    issues,
                    errors,
                    code="input_format_incompatible",
                    message=f"{step.id}: input format {input_format} is incompatible with {step.skill}",
                    step_id=step.id,
                    skill=step.skill,
                    reference=item.ref,
                    expected=expected,
                    observed=input_format,
                    hint=f"Provide a {'/'.join(value.upper() for value in expected)} input or choose a skill compatible with {str(input_format).upper()}.",
                )
        step_output_names: set[str] = set()
        for output in step.outputs:
            if output.name in reserved_step_ids:
                _add_issue(
                    issues,
                    errors,
                    code="output_name_reserved",
                    message=f"{step.id}: output name {output.name} collides with a step id",
                    step_id=step.id,
                    skill=step.skill,
                    reference=output.name,
                    hint="Rename the output so it does not match any step_XX identifier.",
                )
            if output.name in step_output_names:
                _add_issue(
                    issues,
                    errors,
                    code="duplicate_step_output",
                    message=f"{step.id}: duplicate output name {output.name}",
                    step_id=step.id,
                    skill=step.skill,
                    reference=output.name,
                    hint="Give every output within a step a unique name.",
                )
            step_output_names.add(output.name)
            if output.format not in skill.output_formats:
                _add_issue(
                    issues,
                    errors,
                    code="output_format_incompatible",
                    message=f"{step.id}: output format {output.format} is incompatible with {step.skill}",
                    step_id=step.id,
                    skill=step.skill,
                    reference=output.name,
                    expected=sorted(skill.output_formats),
                    observed=output.format,
                    hint="Use an output format declared by the registered skill contract.",
                )
            available_outputs[f"{step.id}.{output.name}"] = output.format
            output_aliases.setdefault(output.name, []).append(
                (f"{step.id}.{output.name}", output.format)
            )
        available_outputs[step.id] = "directory"
        _validate_parameters(
            step.parameters,
            skill.parameter_schema,
            step.id,
            step.skill,
            errors,
            issues,
        )
        if (
            check_dependencies
            and len(issues) == step_issue_start
            and step.skill not in readiness_checked
        ):
            readiness_checked.add(step.skill)
            readiness_check = getattr(skill, "check_readiness", None)
            if callable(readiness_check):
                try:
                    readiness = readiness_check()
                except Exception as exc:
                    readiness = {"ready": False, "error": str(exc)}
                if not readiness.get("ready", False):
                    issue_code = readiness.get("issue_code", "dependency_missing")
                    instructions = readiness.get("installation_instructions", [])
                    if issue_code == "skill_not_configured":
                        hint = str(readiness.get("error", "Configure the skill adapter."))
                        message = f"{step.id}: {step.skill} is registered but not configured for execution"
                    else:
                        hint = " ".join(str(item) for item in instructions) or str(
                            readiness.get(
                                "error",
                                "Install or configure the required dependency, then restart PaleoRigor.",
                            )
                        )
                        message = (
                            f"{step.id}: required dependency is unavailable "
                            f"for {step.skill}: "
                            f"{readiness.get('tool') or readiness.get('dependency') or step.skill}"
                        )
                    tool = (
                        readiness.get("tool")
                        or readiness.get("dependency")
                        or step.skill
                    )
                    _add_issue(
                        issues,
                        errors,
                        code=issue_code,
                        message=message,
                        step_id=step.id,
                        skill=step.skill,
                        observed=tool,
                        hint=hint,
                    )
        if skill.resource_class == "heavy":
            warnings.append(f"{step.id}: heavy resource requirement")
    return ValidationReport(not errors, errors, warnings, issues)

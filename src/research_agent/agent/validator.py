from dataclasses import dataclass
from typing import Any

from research_agent.agent.models import Workflow
from research_agent.agent.refs import normalize_step_ref


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: list[str]
    warnings: list[str]


def _validate_parameters(value: Any, schema: dict[str, Any], name: str, errors: list[str]) -> None:
    required = schema.get("required", [])
    for key in required:
        if key not in value:
            errors.append(f"{name}: missing parameter {key}")
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        for key in value:
            if key not in allowed:
                errors.append(f"{name}: unsupported parameter {key}")
    for key, field_schema in schema.get("properties", {}).items():
        if key not in value:
            continue
        field_value = value[key]
        if "enum" in field_schema and field_value not in field_schema["enum"]:
            errors.append(f"{name}: invalid value for {key}")
        field_type = field_schema.get("type")
        if field_type == "integer" and (
            not isinstance(field_value, int) or isinstance(field_value, bool)
        ):
            errors.append(f"{name}: {key} must be an integer")
            continue
        if field_type == "string" and not isinstance(field_value, str):
            errors.append(f"{name}: {key} must be a string")
            continue
        if field_type == "boolean" and not isinstance(field_value, bool):
            errors.append(f"{name}: {key} must be a boolean")
            continue
        if field_type == "number" and (
            not isinstance(field_value, (int, float))
            or isinstance(field_value, bool)
        ):
            errors.append(f"{name}: {key} must be a number")
            continue
        if field_type == "array":
            if not isinstance(field_value, list):
                errors.append(f"{name}: {key} must be an array")
                continue
            if len(field_value) < field_schema.get("minItems", 0):
                errors.append(f"{name}: too few items in {key}")
            item_schema = field_schema.get("items", {})
            if "enum" in item_schema:
                for item in field_value:
                    if item not in item_schema["enum"]:
                        errors.append(f"{name}: invalid item in {key}")
                        break
        if "minimum" in field_schema and field_value < field_schema["minimum"]:
            errors.append(f"{name}: {key} is below minimum")
        if "maximum" in field_schema and field_value > field_schema["maximum"]:
            errors.append(f"{name}: {key} is above maximum")


def _format_is_compatible(input_format: str, accepted_formats: set[str]) -> bool:
    return "any" in accepted_formats or input_format in accepted_formats


def validate_workflow(workflow: Workflow, registry, uploaded_formats: dict[str, str]) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    available_outputs: dict[str, str] = {}
    for step in workflow.steps:
        if step.id in seen_ids:
            errors.append(f"Duplicate step id: {step.id}")
        seen_ids.add(step.id)
        try:
            skill = registry.get(step.skill)
        except KeyError:
            errors.append(f"Unknown skill: {step.skill}")
            continue
        for item in step.inputs:
            if item.source == "uploaded":
                input_format = uploaded_formats.get(item.ref)
                if input_format is None:
                    errors.append(f"{step.id}: missing uploaded input {item.ref}")
                    continue
            else:
                input_format = available_outputs.get(normalize_step_ref(item.ref))
                if input_format is None:
                    errors.append(f"{step.id}: missing earlier step output {item.ref}")
                    continue
            if not _format_is_compatible(input_format, skill.input_formats):
                errors.append(f"{step.id}: input format {input_format} is incompatible with {step.skill}")
        for output in step.outputs:
            if output.format not in skill.output_formats:
                errors.append(f"{step.id}: output format {output.format} is incompatible with {step.skill}")
            available_outputs[f"{step.id}.{output.name}"] = output.format
            available_outputs[output.name] = output.format
        available_outputs[step.id] = "directory"
        _validate_parameters(step.parameters, skill.parameter_schema, step.id, errors)
        if skill.resource_class == "heavy":
            warnings.append(f"{step.id}: heavy resource requirement")
    return ValidationReport(not errors, errors, warnings)

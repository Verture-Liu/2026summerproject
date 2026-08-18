from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from research_agent.agent.models import Workflow
from research_agent.agent.prompts import build_system_prompt
from research_agent.skills.registry import build_default_registry

from .scenarios import Scenario


BLOCKED_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "reason_code", "message"],
    "properties": {
        "status": {"const": "blocked"},
        "reason_code": {
            "enum": [
                "file_type_mismatch",
                "missing_mate",
                "unsupported_scientific_claim",
                "missing_prerequisite",
            ]
        },
        "message": {"type": "string", "minLength": 1},
    },
}


def _common_contract(scenario: Scenario) -> str:
    catalog = [asdict(item) for item in build_default_registry().catalog()]
    return "\n".join(
        [
            f"WORKFLOW_JSON_SCHEMA={json.dumps(Workflow.model_json_schema(), ensure_ascii=False)}",
            f"BLOCKED_JSON_SCHEMA={json.dumps(BLOCKED_JSON_SCHEMA, ensure_ascii=False)}",
            f"FILES={json.dumps(scenario.file_summaries, ensure_ascii=False)}",
            f"AVAILABLE_SKILLS={json.dumps(catalog, ensure_ascii=False)}",
        ]
    )


def build_arm_system_prompt(arm: str, scenario: Scenario) -> str:
    if arm == "raw_llm":
        base = Path(__file__).with_name("prompts").joinpath("raw_system.txt").read_text(encoding="utf-8")
    elif arm == "paleorigor":
        base = build_system_prompt(scenario.file_summaries, build_default_registry().catalog())
        base += "\n" + "\n".join(
            [
                "PALEORIGOR_CONTROL_LAYER=enabled",
                "When the request conflicts with the observed file format, return blocked with reason_code file_type_mismatch; do not substitute another analysis.",
                "When a named paired-end mate is absent, return blocked with reason_code missing_mate; do not invent or reuse a file.",
                "FastQC or general QC cannot prove ancient authenticity or absence of contamination. Return blocked with reason_code unsupported_scientific_claim for such proof requests.",
                "mapDamage and DamageProfiler require aligned BAM data and an explicit valid reference workflow. If prerequisites are absent, return blocked with reason_code missing_prerequisite; never choose an arbitrary reference.",
                "A blocked decision is valid JSON and takes precedence over the workflow-only wording above when a scientific or input boundary is reached.",
            ]
        )
    else:
        raise ValueError(f"Unknown arm: {arm}")
    return f"{base.rstrip()}\n{_common_contract(scenario)}"

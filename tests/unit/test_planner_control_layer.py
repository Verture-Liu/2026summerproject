"""The desktop planner runs with the same control layer the frozen evaluation tested,
and a refusal comes back as a typed blocked decision instead of a workflow."""
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from pydantic import ValidationError

from research_agent.agent.models import BLOCKED_REASON_CODES, BlockedDecision, Workflow
from research_agent.agent.planner import Planner
from research_agent.agent.prompts import (
    BLOCKED_JSON_SCHEMA,
    CONTROL_LAYER_RULES,
    build_planner_prompt,
    build_system_prompt,
)


EVALUATED_PREFIX = Path("supplementary/file_4_system_prompts/paleorigor_only_prefix.txt")


def completion(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def planner_for(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client, Planner(client=client, base_url="https://example.test/v1", api_key="control-layer-key", model="m")


def test_blocked_decision_accepts_only_the_four_reason_codes():
    for code in BLOCKED_REASON_CODES:
        decision = BlockedDecision.model_validate({"status": "blocked", "reason_code": code, "message": "stop"})
        assert decision.reason_code == code
    with pytest.raises(ValidationError):
        BlockedDecision.model_validate({"status": "blocked", "reason_code": "other", "message": "stop"})
    with pytest.raises(ValidationError):
        BlockedDecision.model_validate({"status": "blocked", "reason_code": "missing_mate", "message": ""})
    with pytest.raises(ValidationError):
        BlockedDecision.model_validate(
            {"status": "blocked", "reason_code": "missing_mate", "message": "stop", "workflow": {}}
        )


def test_blocked_schema_and_model_name_the_same_reason_codes():
    assert tuple(BLOCKED_JSON_SCHEMA["properties"]["reason_code"]["enum"]) == BLOCKED_REASON_CODES


def test_planner_prompt_is_the_workflow_contract_plus_the_control_layer():
    files = [{"ref": "reads", "format": "fastq", "name": "reads.fastq.gz"}]
    prompt = build_planner_prompt(files, [])
    assert prompt.startswith(build_system_prompt(files, []))
    for rule in CONTROL_LAYER_RULES:
        assert rule in prompt
    assert f"BLOCKED_JSON_SCHEMA={json.dumps(BLOCKED_JSON_SCHEMA, ensure_ascii=False)}" in prompt


def test_control_layer_rules_are_the_ones_the_evaluation_used():
    evaluated_lines = EVALUATED_PREFIX.read_text(encoding="utf-8").splitlines()
    for rule in CONTROL_LAYER_RULES:
        assert rule in evaluated_lines


def test_control_layer_matches_the_benchmark_paleorigor_arm():
    from analysis.benchmark_v2.prompts import BLOCKED_JSON_SCHEMA as benchmark_schema
    from analysis.benchmark_v2.prompts import build_arm_system_prompt

    assert benchmark_schema == BLOCKED_JSON_SCHEMA
    arm_lines = build_arm_system_prompt("paleorigor", SimpleNamespace(file_summaries=[])).splitlines()
    for rule in CONTROL_LAYER_RULES:
        assert rule in arm_lines


@pytest.mark.asyncio
async def test_planner_returns_a_blocked_decision_and_sends_the_control_layer():
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return completion(json.dumps({
            "status": "blocked",
            "reason_code": "unsupported_scientific_claim",
            "message": "FastQC output cannot show that these reads are ancient.",
        }))

    client, planner = planner_for(handler)
    result = await planner.plan("Prove these reads are ancient and uncontaminated.", [], [])
    await client.aclose()

    assert isinstance(result, BlockedDecision)
    assert result.reason_code == "unsupported_scientific_claim"
    assert len(sent) == 1
    system_prompt = sent[0]["messages"][0]["content"]
    assert "PALEORIGOR_CONTROL_LAYER=enabled" in system_prompt
    assert "BLOCKED_JSON_SCHEMA=" in system_prompt


@pytest.mark.asyncio
async def test_planner_still_returns_workflows_for_supported_requests():
    workflow = {
        "schema_version": "1.0",
        "task_summary": "filter",
        "steps": [{
            "id": "step_01", "skill": "peptide_filter",
            "inputs": [{"source": "uploaded", "ref": "peptides"}],
            "parameters": {"min_length": 13, "max_length": 26},
            "outputs": [{"name": "filtered", "format": "fasta"}],
            "reason": "length filter",
        }],
    }
    client, planner = planner_for(lambda request: completion(json.dumps(workflow)))
    result = await planner.plan("filter peptides", [], [])
    await client.aclose()
    assert isinstance(result, Workflow)


@pytest.mark.asyncio
async def test_an_invalid_blocked_decision_goes_through_the_single_repair_call():
    replies = iter([
        json.dumps({"status": "blocked", "reason_code": "not_a_code", "message": "stop"}),
        json.dumps({"status": "blocked", "reason_code": "missing_mate", "message": "R2 was not uploaded."}),
    ])
    calls = []

    def handler(request):
        calls.append(request)
        return completion(next(replies))

    client, planner = planner_for(handler)
    result = await planner.plan("run QC on both mates", [], [])
    await client.aclose()
    assert len(calls) == 2
    assert isinstance(result, BlockedDecision)
    assert result.reason_code == "missing_mate"


@pytest.mark.asyncio
async def test_a_blocked_decision_that_echoes_the_key_is_rejected():
    client, planner = planner_for(lambda request: completion(json.dumps({
        "status": "blocked", "reason_code": "missing_mate", "message": "key control-layer-key",
    })))
    with pytest.raises(Exception):
        await planner.plan("run QC", [], [])
    await client.aclose()

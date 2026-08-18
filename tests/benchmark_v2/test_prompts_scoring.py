import json
from pathlib import Path

from analysis.benchmark_v2.prompts import build_arm_system_prompt
from analysis.benchmark_v2.scenarios import load_scenarios
from analysis.benchmark_v2.scoring import score_completion


ROOT = Path(__file__).resolve().parents[2]


def test_both_arms_share_contract_but_only_paleorigor_gets_domain_rules():
    scenario = load_scenarios(ROOT)[2]
    raw = build_arm_system_prompt("raw_llm", scenario)
    full = build_arm_system_prompt("paleorigor", scenario)
    for marker in ["WORKFLOW_JSON_SCHEMA=", "BLOCKED_JSON_SCHEMA=", "FILES=", "AVAILABLE_SKILLS="]:
        assert marker in raw
        assert marker in full
    assert "PALEORIGOR_CONTROL_LAYER" not in raw
    assert "PALEORIGOR_CONTROL_LAYER" in full


def test_correct_boundary_block_is_strict_success():
    scenario = load_scenarios(ROOT)[2]
    completion = json.dumps({"status": "blocked", "reason_code": "file_type_mismatch", "message": "The uploaded file is CSV, not FASTQ."})
    score = score_completion(completion, scenario)
    assert score.strict_success is True
    assert score.decision == "blocked"


def test_substitute_workflow_fails_boundary_contract():
    scenario = load_scenarios(ROOT)[2]
    completion = json.dumps({
        "schema_version": "1.0", "task_summary": "Analyze the CSV instead",
        "steps": [{"id": "step_01", "skill": "peptide_csv_normalize", "inputs": [{"source": "uploaded", "ref": "Validation.csv"}], "parameters": {}, "outputs": [{"name": "normalized", "format": "csv"}], "reason": "Substitute analysis"}]
    })
    score = score_completion(completion, scenario)
    assert score.strict_success is False
    assert "boundary_requires_block" in score.failure_codes


def test_supported_plan_requires_named_functions():
    scenario = load_scenarios(ROOT)[0]
    completion = json.dumps({
        "schema_version": "1.0", "task_summary": "QC",
        "steps": [{"id": "step_01", "skill": "fastq_qc", "inputs": [{"source": "uploaded", "ref": "ERR3250149.fastq.gz"}], "parameters": {}, "outputs": [{"name": "qc", "format": "html"}], "reason": "QC"}]
    })
    score = score_completion(completion, scenario)
    assert score.strict_success is False
    assert "missing_required_skill:seqkit_stats" in score.failure_codes

from pathlib import Path

from research_agent.agent.models import Workflow
from research_agent.execution.executor import execute_workflow
from research_agent.skills.registry import build_default_registry


def test_executor_runs_approved_workflow(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    source = inputs / "peptides.fasta"
    source.write_text(">a\nAAAAAAAAAAAAA\n>b\nAAAA\n", encoding="utf-8")
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "filter peptides",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_filter",
                    "inputs": [{"source": "uploaded", "ref": "peptides"}],
                    "parameters": {"min_length": 13, "max_length": 26},
                    "outputs": [{"name": "filtered", "format": "fasta"}],
                    "reason": "length filter",
                }
            ],
        }
    )
    summary = execute_workflow(
        workflow=workflow,
        task_dir=tmp_path,
        uploaded_files={"peptides": source},
        registry=build_default_registry(),
        settings={"api_key": "***"},
    )
    assert summary.status == "succeeded"
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "report.html").exists()
    assert Path(summary.outputs[0]).exists()


def test_executor_resolves_step_output_name_references(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    source = inputs / "Validation.csv"
    source.write_text("1,ACDEFGHIKLMNP\n0,AAAAAAAAAAAAA\n", encoding="utf-8")
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "normalize and validate peptides",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_csv_normalize",
                    "inputs": [{"source": "uploaded", "ref": "validation"}],
                    "parameters": {},
                    "outputs": [{"name": "normalized_csv", "format": "csv"}],
                    "reason": "normalize raw peptide csv",
                },
                {
                    "id": "step_02",
                    "skill": "peptide_validate",
                    "inputs": [{"source": "step", "ref": "step_01/normalized_csv"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "validated_csv", "format": "csv"},
                        {"name": "rejected_csv", "format": "csv"},
                    ],
                    "reason": "validate normalized peptide csv",
                },
            ],
        }
    )
    summary = execute_workflow(
        workflow=workflow,
        task_dir=tmp_path / "task",
        uploaded_files={"validation": source},
        registry=build_default_registry(),
        settings={"api_key": ""},
    )
    assert summary.status == "succeeded"
    assert Path(summary.outputs[0]).name == "valid_peptides.csv"

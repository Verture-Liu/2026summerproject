import pytest
from pydantic import ValidationError

from research_agent.agent.models import Workflow


def test_workflow_accepts_registered_shape():
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
                    "reason": "retain synthesis-compatible peptides",
                }
            ],
        }
    )
    assert workflow.steps[0].skill == "peptide_filter"


def test_workflow_rejects_command_field():
    with pytest.raises(ValidationError):
        Workflow.model_validate(
            {
                "schema_version": "1.0",
                "task_summary": "unsafe",
                "steps": [
                    {
                        "id": "step_01",
                        "skill": "x",
                        "inputs": [],
                        "parameters": {},
                        "outputs": [],
                        "reason": "unsafe",
                        "command": "rm -rf /",
                    }
                ],
            }
        )

import hashlib
from pathlib import Path

import pandas as pd

from research_agent.agent.models import Workflow
from research_agent.execution.executor import execute_workflow
from research_agent.skills.registry import build_default_registry


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_executor_runs_complete_peptide_csv_workflow(tmp_path):
    source = tmp_path / "Validation.csv"
    source.write_text(
        "\n".join(
            [
                f"1,{'A' * 13}",
                f"1,{'A' * 13}",
                f"1,{'C' * 26}",
                f"1,{'D' * 27}",
                f"0,{'E' * 20}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    original_hash = digest(source)
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "Filter positive AMPLiT validation peptides",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_csv_normalize",
                    "inputs": [{"source": "uploaded", "ref": "validation"}],
                    "parameters": {},
                    "outputs": [{"name": "normalized", "format": "csv"}],
                    "reason": "Normalize the headerless CSV.",
                },
                {
                    "id": "step_02",
                    "skill": "peptide_validate",
                    "inputs": [{"source": "step", "ref": "step_01.normalized"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "valid", "format": "csv"},
                        {"name": "rejected", "format": "csv"},
                    ],
                    "reason": "Validate peptide rows.",
                },
                {
                    "id": "step_03",
                    "skill": "peptide_label_filter",
                    "inputs": [{"source": "step", "ref": "step_02.valid"}],
                    "parameters": {"labels": [1]},
                    "outputs": [{"name": "positive", "format": "csv"}],
                    "reason": "Keep positive labels.",
                },
                {
                    "id": "step_04",
                    "skill": "peptide_length_filter",
                    "inputs": [{"source": "step", "ref": "step_03.positive"}],
                    "parameters": {"min_length": 13, "max_length": 26},
                    "outputs": [{"name": "length_filtered", "format": "csv"}],
                    "reason": "Keep synthesis-length peptides.",
                },
                {
                    "id": "step_05",
                    "skill": "peptide_deduplicate",
                    "inputs": [{"source": "step", "ref": "step_04.length_filtered"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "deduplicated", "format": "csv"},
                        {"name": "duplicates", "format": "csv"},
                    ],
                    "reason": "Remove duplicate sequences.",
                },
                {
                    "id": "step_06",
                    "skill": "peptide_statistics",
                    "inputs": [{"source": "step", "ref": "step_05.deduplicated"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "statistics", "format": "json"},
                        {"name": "lengths", "format": "csv"},
                        {"name": "composition", "format": "csv"},
                    ],
                    "reason": "Summarize the retained peptides.",
                },
                {
                    "id": "step_07",
                    "skill": "peptide_chart",
                    "inputs": [{"source": "step", "ref": "step_05.deduplicated"}],
                    "parameters": {"charts": ["length_histogram", "label_counts"]},
                    "outputs": [
                        {"name": "length_chart", "format": "png"},
                        {"name": "label_chart", "format": "png"},
                    ],
                    "reason": "Plot diagnostic distributions.",
                },
                {
                    "id": "step_08",
                    "skill": "peptide_csv_export",
                    "inputs": [{"source": "step", "ref": "step_05.deduplicated"}],
                    "parameters": {"filename": "final_peptides.csv"},
                    "outputs": [{"name": "final", "format": "csv"}],
                    "reason": "Export the final table.",
                },
            ],
        }
    )
    summary = execute_workflow(
        workflow,
        tmp_path / "task",
        {"validation": source},
        build_default_registry(),
        {"api_key": ""},
    )
    assert summary.status == "succeeded"
    final = pd.read_csv(summary.outputs[0])
    assert final["sequence"].tolist() == ["A" * 13, "C" * 26]
    assert digest(source) == original_hash
    assert (tmp_path / "task" / "manifest.json").exists()
    assert (tmp_path / "task" / "report.html").exists()

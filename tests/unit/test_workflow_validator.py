from research_agent.agent.models import Workflow
from research_agent.agent.validator import validate_workflow
from research_agent.skills.registry import build_default_registry


def _workflow(skill="peptide_filter", ref="peptides"):
    return Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "filter",
            "steps": [
                {
                    "id": "step_01",
                    "skill": skill,
                    "inputs": [{"source": "uploaded", "ref": ref}],
                    "parameters": {"min_length": 13, "max_length": 26},
                    "outputs": [{"name": "filtered", "format": "fasta"}],
                    "reason": "filter lengths",
                }
            ],
        }
    )


def test_validator_rejects_unknown_skill():
    report = validate_workflow(_workflow(skill="not_registered"), build_default_registry(), {"peptides": "fasta"})
    assert not report.valid
    assert "Unknown skill" in report.errors[0]


def test_validator_accepts_compatible_workflow():
    report = validate_workflow(_workflow(), build_default_registry(), {"peptides": "fasta"})
    assert report.valid


def test_validator_treats_any_input_format_as_wildcard():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "detect file type",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "file_type_detect",
                    "inputs": [{"source": "uploaded", "ref": "validation"}],
                    "parameters": {},
                    "outputs": [{"name": "file_type_report", "format": "json"}],
                    "reason": "inspect uploaded file format",
                }
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"validation": "csv"}
    )
    assert report.valid


def test_validator_accepts_unique_step_output_name_references():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "normalize then validate",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_csv_normalize",
                    "inputs": [{"source": "uploaded", "ref": "validation"}],
                    "parameters": {},
                    "outputs": [{"name": "normalized_csv", "format": "csv"}],
                    "reason": "normalize csv",
                },
                {
                    "id": "step_02",
                    "skill": "peptide_validate",
                    "inputs": [{"source": "step", "ref": "normalized_csv"}],
                    "parameters": {},
                    "outputs": [{"name": "validated_csv", "format": "csv"}],
                    "reason": "validate peptides",
                },
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"validation": "csv"}
    )
    assert report.valid


def test_validator_accepts_slash_step_output_references():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "normalize then validate",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_csv_normalize",
                    "inputs": [{"source": "uploaded", "ref": "validation"}],
                    "parameters": {},
                    "outputs": [{"name": "normalized", "format": "csv"}],
                    "reason": "normalize csv",
                },
                {
                    "id": "step_02",
                    "skill": "peptide_validate",
                    "inputs": [{"source": "step", "ref": "step_01/normalized"}],
                    "parameters": {},
                    "outputs": [{"name": "validated", "format": "csv"}],
                    "reason": "validate peptides",
                },
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"validation": "csv"}
    )
    assert report.valid


def test_validator_accepts_colon_step_output_references():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "fastq qc then multiqc",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "fastq_qc",
                    "inputs": [{"source": "uploaded", "ref": "reads"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "qc_html", "format": "html"},
                        {"name": "qc_json", "format": "json"},
                        {"name": "qc_zip", "format": "zip"},
                    ],
                    "reason": "run fastqc",
                },
                {
                    "id": "step_02",
                    "skill": "multiqc_summary",
                    "inputs": [{"source": "step", "ref": "step_01:qc_zip"}],
                    "parameters": {},
                    "outputs": [{"name": "multiqc_html", "format": "html"}],
                    "reason": "summarize fastqc",
                },
            ],
        }
    )
    report = validate_workflow(workflow, build_default_registry(), {"reads": "fastq"})
    assert report.valid


def test_validator_accepts_whole_step_directory_references():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "fastq qc then multiqc",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "fastq_qc",
                    "inputs": [{"source": "uploaded", "ref": "reads"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "raw_fastqc_html", "format": "html"},
                        {"name": "raw_fastqc_json", "format": "json"},
                        {"name": "raw_fastqc_zip", "format": "zip"},
                    ],
                    "reason": "run fastqc",
                },
                {
                    "id": "step_02",
                    "skill": "multiqc_summary",
                    "inputs": [{"source": "step", "ref": "step_01"}],
                    "parameters": {},
                    "outputs": [{"name": "multiqc_html", "format": "html"}],
                    "reason": "summarize whole fastqc output folder",
                },
            ],
        }
    )
    report = validate_workflow(workflow, build_default_registry(), {"reads": "fastq"})
    assert report.valid


def test_validator_rejects_invalid_array_items_and_too_few_items():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "filter labels",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_label_filter",
                    "inputs": [{"source": "uploaded", "ref": "peptides"}],
                    "parameters": {"labels": [2]},
                    "outputs": [{"name": "filtered", "format": "csv"}],
                    "reason": "keep requested labels",
                }
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"peptides": "csv"}
    )
    assert not report.valid
    assert "invalid item in labels" in report.errors[0]


def test_validator_rejects_wrong_boolean_type_and_values_above_maximum():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "make chart",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_chart",
                    "inputs": [{"source": "uploaded", "ref": "peptides"}],
                    "parameters": {
                        "charts": ["label_counts"],
                        "width": 2500,
                        "height": 800,
                    },
                    "outputs": [{"name": "chart", "format": "png"}],
                    "reason": "plot labels",
                }
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"peptides": "csv"}
    )
    assert not report.valid
    assert any("width is above maximum" in error for error in report.errors)


def test_validator_rejects_number_above_maximum():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "predict amps",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "amp_prediction",
                    "inputs": [{"source": "uploaded", "ref": "peptides"}],
                    "parameters": {"score_threshold": 1.5},
                    "outputs": [
                        {"name": "predictions", "format": "csv"},
                        {"name": "metadata", "format": "json"},
                    ],
                    "reason": "predict antimicrobial peptides",
                }
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"peptides": "csv"}
    )
    assert not report.valid
    assert any("score_threshold is above maximum" in error for error in report.errors)


def test_validator_rejects_non_numeric_number_parameter():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "predict amps",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "amp_prediction",
                    "inputs": [{"source": "uploaded", "ref": "peptides"}],
                    "parameters": {"score_threshold": "high"},
                    "outputs": [{"name": "predictions", "format": "csv"}],
                    "reason": "predict antimicrobial peptides",
                }
            ],
        }
    )
    report = validate_workflow(
        workflow, build_default_registry(), {"peptides": "csv"}
    )
    assert not report.valid
    assert any("score_threshold must be a number" in error for error in report.errors)

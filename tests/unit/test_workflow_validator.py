from research_agent.agent.models import Workflow
from research_agent.agent.validator import validate_workflow
from research_agent.skills.ancient_dna.fastq_qc import FastqQcSkill
from research_agent.skills.registry import build_default_registry


class _Registry:
    def __init__(self, *skills):
        self.skills = {skill.name: skill for skill in skills}

    def get(self, name):
        if name not in self.skills:
            raise KeyError(name)
        return self.skills[name]


class _ReadySkill:
    name = "ready_skill"
    description = "test skill"
    input_formats = {"csv"}
    output_formats = {"json"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def check_readiness(self):
        return {
            "ready": False,
            "tool": "example-tool",
            "installation_instructions": [
                "Install example-tool in a dedicated conda environment."
            ],
        }


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


def test_validator_reports_actionable_incompatible_input_issue():
    report = validate_workflow(
        _workflow(skill="fastq_qc"),
        build_default_registry(),
        {"peptides": "csv"},
    )

    assert not report.valid
    issue = report.issues[0]
    assert issue.code == "input_format_incompatible"
    assert issue.step_id == "step_01"
    assert issue.skill == "fastq_qc"
    assert issue.reference == "peptides"
    assert issue.expected == ["fastq"]
    assert issue.observed == "csv"
    assert "FASTQ" in issue.hint


def test_validator_rejects_ambiguous_bare_output_reference():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "ambiguous reference",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "file_type_detect",
                    "inputs": [{"source": "uploaded", "ref": "first"}],
                    "parameters": {},
                    "outputs": [{"name": "report", "format": "json"}],
                    "reason": "inspect first file",
                },
                {
                    "id": "step_02",
                    "skill": "file_type_detect",
                    "inputs": [{"source": "uploaded", "ref": "second"}],
                    "parameters": {},
                    "outputs": [{"name": "report", "format": "json"}],
                    "reason": "inspect second file",
                },
                {
                    "id": "step_03",
                    "skill": "data_quality_gate",
                    "inputs": [{"source": "step", "ref": "report"}],
                    "parameters": {"fail_on_error": False},
                    "outputs": [{"name": "gate", "format": "json"}],
                    "reason": "inspect one report",
                },
            ],
        }
    )

    report = validate_workflow(
        workflow,
        build_default_registry(),
        {"first": "csv", "second": "csv"},
    )

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "ambiguous_step_output")
    assert issue.reference == "report"
    assert issue.expected == ["step_01.report", "step_02.report"]
    assert "qualified" in issue.hint.lower()


def test_validator_reports_missing_dependency_before_execution():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "dependency check",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "ready_skill",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {},
                    "outputs": [{"name": "report", "format": "json"}],
                    "reason": "run dependency-backed skill",
                }
            ],
        }
    )

    report = validate_workflow(
        workflow,
        _Registry(_ReadySkill()),
        {"table": "csv"},
        check_dependencies=True,
    )

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "dependency_missing")
    assert issue.skill == "ready_skill"
    assert issue.observed == "example-tool"
    assert "Install example-tool" in issue.hint


def test_validator_skips_dependency_noise_for_invalid_input_contract():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "wrong input before dependency check",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "ready_skill",
                    "inputs": [{"source": "uploaded", "ref": "reads"}],
                    "parameters": {},
                    "outputs": [{"name": "report", "format": "json"}],
                    "reason": "test validation order",
                }
            ],
        }
    )

    report = validate_workflow(
        workflow,
        _Registry(_ReadySkill()),
        {"reads": "fastq"},
        check_dependencies=True,
    )

    assert [issue.code for issue in report.issues] == ["input_format_incompatible"]


def test_validator_rejects_indexed_upload_whose_staged_file_is_missing(tmp_path):
    missing = tmp_path / "deleted.csv"

    report = validate_workflow(
        _workflow(skill="peptide_csv_normalize", ref="table"),
        build_default_registry(),
        {"table": "csv"},
        uploaded_paths={"table": missing},
    )

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "uploaded_file_missing")
    assert issue.reference == "table"
    assert issue.observed == str(missing)


def test_fastq_qc_exposes_real_dependency_readiness(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.resolve_tool",
        lambda candidates: None,
    )

    readiness = FastqQcSkill().check_readiness()

    assert readiness["ready"] is False
    assert readiness["tool"] == "FastQC"
    assert "fastqc --version" in " ".join(readiness["installation_instructions"])


def test_validator_rejects_duplicate_output_names_within_step():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "duplicate outputs",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "file_type_detect",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "report", "format": "json"},
                        {"name": "report", "format": "json"},
                    ],
                    "reason": "inspect input",
                }
            ],
        }
    )

    report = validate_workflow(workflow, build_default_registry(), {"table": "csv"})

    assert not report.valid
    assert any(issue.code == "duplicate_step_output" for issue in report.issues)


def test_validator_enforces_exclusive_minimum_parameter():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "invalid sampling fraction",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "seqtk_sample",
                    "inputs": [{"source": "uploaded", "ref": "reads"}],
                    "parameters": {"fraction": 0, "seed": 11},
                    "outputs": [{"name": "sampled", "format": "fastq"}],
                    "reason": "subsample reads",
                }
            ],
        }
    )

    report = validate_workflow(workflow, build_default_registry(), {"reads": "fastq"})

    assert not report.valid
    issue = next(
        item
        for item in report.issues
        if item.code == "parameter_invalid" and item.parameter == "fraction"
    )
    assert issue.expected == "> 0"


def test_validator_rejects_missing_required_inputs():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "missing input",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "fastq_qc",
                    "inputs": [],
                    "parameters": {},
                    "outputs": [{"name": "qc_html", "format": "html"}],
                    "reason": "run quality control",
                }
            ],
        }
    )

    report = validate_workflow(workflow, build_default_registry(), {})

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "input_count_invalid")
    assert issue.expected == {"minimum": 1, "maximum": None}
    assert issue.observed == 0


def test_validator_rejects_too_many_inputs_for_bounded_skill():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "too many host-removal inputs",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "host_dna_removal",
                    "inputs": [
                        {"source": "uploaded", "ref": "r1"},
                        {"source": "uploaded", "ref": "r2"},
                        {"source": "uploaded", "ref": "r3"},
                    ],
                    "parameters": {"reference": "human_index"},
                    "outputs": [{"name": "cleaned", "format": "fastq"}],
                    "reason": "remove host reads",
                }
            ],
        }
    )

    report = validate_workflow(
        workflow,
        build_default_registry(),
        {"r1": "fastq", "r2": "fastq", "r3": "fastq"},
    )

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "input_count_invalid")
    assert issue.expected == {"minimum": 1, "maximum": 2}
    assert issue.observed == 3


def test_validator_rejects_output_alias_that_collides_with_step_id():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "reserved alias collision",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "file_type_detect",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {},
                    "outputs": [{"name": "step_02", "format": "json"}],
                    "reason": "create a colliding alias",
                },
                {
                    "id": "step_02",
                    "skill": "data_quality_gate",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {"fail_on_error": False},
                    "outputs": [{"name": "gate", "format": "json"}],
                    "reason": "create the colliding step directory",
                },
            ],
        }
    )

    report = validate_workflow(workflow, build_default_registry(), {"table": "csv"})

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "output_name_reserved")
    assert issue.reference == "step_02"


def test_single_input_skill_rejects_extra_inputs_by_default():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "two tables sent to one-table validator",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "peptide_validate",
                    "inputs": [
                        {"source": "uploaded", "ref": "first"},
                        {"source": "uploaded", "ref": "second"},
                    ],
                    "parameters": {},
                    "outputs": [{"name": "valid", "format": "csv"}],
                    "reason": "validate peptides",
                }
            ],
        }
    )

    report = validate_workflow(
        workflow,
        build_default_registry(),
        {"first": "csv", "second": "csv"},
    )

    assert not report.valid
    issue = next(item for item in report.issues if item.code == "input_count_invalid")
    assert issue.expected == {"minimum": 1, "maximum": 1}


def test_validator_enforces_minimum_string_length():
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "empty reference index",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "bowtie2_align",
                    "inputs": [{"source": "uploaded", "ref": "reads"}],
                    "parameters": {"index": ""},
                    "outputs": [{"name": "alignment", "format": "sam"}],
                    "reason": "align reads",
                }
            ],
        }
    )

    report = validate_workflow(workflow, build_default_registry(), {"reads": "fastq"})

    assert not report.valid
    issue = next(
        item
        for item in report.issues
        if item.code == "parameter_invalid" and item.parameter == "index"
    )
    assert issue.expected == "length >= 1"


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

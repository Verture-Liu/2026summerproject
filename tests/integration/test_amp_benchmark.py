from research_agent.agent.models import Workflow
from research_agent.agent.validator import validate_workflow
from research_agent.benchmarks.amp_score import score_workflow
from research_agent.skills.registry import build_default_registry


def _reference():
    return Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "AMP benchmark",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "fastq_quality_filter",
                    "inputs": [{"source": "uploaded", "ref": "stool_reads"}],
                    "parameters": {"min_length": 30},
                    "outputs": [{"name": "filtered", "format": "fastq"}],
                    "reason": "remove short reads",
                },
                {
                    "id": "step_02",
                    "skill": "metagenome_assembly",
                    "inputs": [{"source": "step", "ref": "step_01.filtered"}],
                    "parameters": {"mode": "meta"},
                    "outputs": [{"name": "contigs", "format": "fasta"}],
                    "reason": "assemble contigs",
                },
            ],
        }
    )


def test_amp_planning_score_detects_missing_assembly():
    reference = _reference()
    candidate = Workflow(
        schema_version="1.0",
        task_summary="candidate",
        steps=[reference.steps[0]],
    )
    score = score_workflow(candidate, reference)
    assert score.step_recall == 0.5
    assert score.missing_skills == ["metagenome_assembly"]


def test_full_amp_reference_workflow_is_registered():
    reference = Workflow.model_validate_json(
        open(
            "src/research_agent/benchmarks/amp_workflow.json",
            encoding="utf-8",
        ).read()
    )
    report = validate_workflow(
        reference,
        build_default_registry(),
        {"stool_reads": "fastq", "environment_reads": "fastq"},
    )
    assert report.valid, report.errors

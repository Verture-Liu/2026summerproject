from pathlib import Path

from research_agent.agent.models import Workflow
from research_agent.execution.executor import _path_matches_format, execute_workflow
from research_agent.skills.base import SkillResult


class FakeSkill:
    def run(self, context, parameters):
        html = context.work_dir / "sample_fastqc.html"
        metadata = context.work_dir / "fastqc_run_metadata.json"
        zip_report = context.work_dir / "sample_fastqc.zip"
        html.write_text("<html>FastQC</html>", encoding="utf-8")
        metadata.write_text("{}", encoding="utf-8")
        zip_report.write_bytes(b"zip")
        return SkillResult("succeeded", [str(html), str(metadata), str(zip_report)], {}, [])


class FakeRegistry:
    def get(self, name):
        return FakeSkill()


class WrongFormatSkill:
    def run(self, context, parameters):
        metadata = context.work_dir / "only_metadata.json"
        metadata.write_text("{}", encoding="utf-8")
        return SkillResult("succeeded", [str(metadata)], {}, [])


class WrongFormatRegistry:
    def get(self, name):
        return WrongFormatSkill()


class AmbiguousCsvSkill:
    def run(self, context, parameters):
        first = context.work_dir / "first.csv"
        second = context.work_dir / "second.csv"
        first.write_text("value\nfirst\n", encoding="utf-8")
        second.write_text("value\nsecond\n", encoding="utf-8")
        return SkillResult("succeeded", [str(first), str(second)], {}, [])


class AmbiguousCsvRegistry:
    def get(self, name):
        return AmbiguousCsvSkill()


def test_executor_maps_equal_count_same_format_outputs_in_declared_order(tmp_path):
    uploaded = tmp_path / "table.csv"
    uploaded.write_text("value\ninput\n", encoding="utf-8")
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "two named tables",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "two_csv_outputs",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {},
                    "outputs": [
                        {"name": "first_table", "format": "csv"},
                        {"name": "second_table", "format": "csv"},
                    ],
                    "reason": "map complete ordered output set",
                }
            ],
        }
    )

    summary = execute_workflow(
        workflow,
        tmp_path / "task",
        {"table": uploaded},
        AmbiguousCsvRegistry(),
        {},
    )

    assert summary.status == "succeeded"


def test_executor_maps_declared_outputs_by_format_when_skill_returns_extra_files(tmp_path):
    uploaded = tmp_path / "reads.fastq.gz"
    uploaded.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "fastqc zip only",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "fastq_qc",
                    "inputs": [{"source": "uploaded", "ref": "reads"}],
                    "parameters": {},
                    "outputs": [{"name": "fastqc_zip", "format": "zip"}],
                    "reason": "run fastqc",
                },
                {
                    "id": "step_02",
                    "skill": "multiqc_summary",
                    "inputs": [{"source": "step", "ref": "step_01.fastqc_zip"}],
                    "parameters": {},
                    "outputs": [{"name": "multiqc_html", "format": "html"}],
                    "reason": "use fastqc zip",
                },
            ],
        }
    )

    summary = execute_workflow(
        workflow,
        tmp_path / "task",
        {"reads": uploaded},
        FakeRegistry(),
        {},
    )

    assert summary.steps[1]["status"] == "succeeded"
    assert summary.steps[1]["inputs"] == [str(tmp_path / "task" / "steps" / "step_01" / "sample_fastqc.zip")]


def test_executor_fails_when_skill_does_not_produce_declared_format(tmp_path):
    uploaded = tmp_path / "table.csv"
    uploaded.write_text("a,b\n1,2\n", encoding="utf-8")
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "require csv output",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "conditional_export",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {},
                    "outputs": [{"name": "cleaned", "format": "csv"}],
                    "reason": "export cleaned table",
                }
            ],
        }
    )

    summary = execute_workflow(
        workflow,
        tmp_path / "task",
        {"table": uploaded},
        WrongFormatRegistry(),
        {},
    )

    assert summary.status == "failed"
    assert summary.steps[0]["status"] == "failed"
    assert "did not produce declared output cleaned (csv)" in summary.steps[0]["error"]


def test_fastq_format_does_not_accept_arbitrary_gzip_file(tmp_path):
    archive = tmp_path / "results.tar.gz"
    archive.write_bytes(b"not a fastq")

    assert not _path_matches_format(archive, "fastq")
    assert _path_matches_format(tmp_path / "reads.fastq.gz", "fastq")
    assert _path_matches_format(tmp_path / "reads.fq.gz", "fastq")


def test_executor_rejects_ambiguous_same_format_output_alias(tmp_path):
    uploaded = tmp_path / "table.csv"
    uploaded.write_text("value\ninput\n", encoding="utf-8")
    workflow = Workflow.model_validate(
        {
            "schema_version": "1.0",
            "task_summary": "ambiguous output mapping",
            "steps": [
                {
                    "id": "step_01",
                    "skill": "two_csv_outputs",
                    "inputs": [{"source": "uploaded", "ref": "table"}],
                    "parameters": {},
                    "outputs": [{"name": "audit", "format": "csv"}],
                    "reason": "ensure ambiguous aliases fail closed",
                }
            ],
        }
    )

    summary = execute_workflow(
        workflow,
        tmp_path / "task",
        {"table": uploaded},
        AmbiguousCsvRegistry(),
        {},
    )

    assert summary.status == "failed"
    assert "ambiguous declared output audit (csv)" in summary.steps[0]["error"]

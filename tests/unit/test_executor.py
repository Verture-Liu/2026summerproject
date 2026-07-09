from pathlib import Path

from research_agent.agent.models import Workflow
from research_agent.execution.executor import execute_workflow
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

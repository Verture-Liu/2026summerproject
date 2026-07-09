import json
from pathlib import Path

import pandas as pd

from research_agent.skills.conda_tools import ToolCommand
from research_agent.skills.base import SkillContext
from research_agent.skills.workflow_utilities import (
    FastqPairMatchSkill,
    FileTypeDetectSkill,
    SampleSheetValidateSkill,
    ToolEnvironmentCheckSkill,
    MultiqcSummarySkill,
)


def test_file_type_detect_identifies_fastq_and_csv(tmp_path):
    fastq = tmp_path / "reads.fastq"
    fastq.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")
    csv = tmp_path / "samples.csv"
    csv.write_text("sample_id,fastq_1\nS1,reads.fastq\n", encoding="utf-8")

    result = FileTypeDetectSkill().run(SkillContext(tmp_path / "work", [fastq, csv]), {})

    assert result.status == "succeeded"
    report = json.loads(Path(result.outputs[0]).read_text(encoding="utf-8"))
    assert [item["format"] for item in report["files"]] == ["fastq", "csv"]


def test_fastq_pair_match_writes_sample_pairs(tmp_path):
    r1 = tmp_path / "sampleA_R1.fastq.gz"
    r2 = tmp_path / "sampleA_R2.fastq.gz"
    single = tmp_path / "sampleB.fastq.gz"
    for path in (r1, r2, single):
        path.write_text("", encoding="utf-8")

    result = FastqPairMatchSkill().run(
        SkillContext(tmp_path / "work", [r1, r2, single]),
        {},
    )

    assert result.status == "succeeded"
    rows = pd.read_csv(result.outputs[0], keep_default_na=False).to_dict("records")
    assert rows == [
        {
            "sample_id": "sampleA",
            "layout": "paired",
            "fastq_1": str(r1.resolve()),
            "fastq_2": str(r2.resolve()),
        },
        {
            "sample_id": "sampleB",
            "layout": "single",
            "fastq_1": str(single.resolve()),
            "fastq_2": "",
        },
    ]


def test_tool_environment_check_reports_missing_tools(tmp_path, monkeypatch):
    def fake_resolve_tool(names):
        name = names[0]
        if name == "gzip":
            return ToolCommand("gzip", ["/usr/bin/gzip"], "path")
        return None

    monkeypatch.setattr("research_agent.skills.workflow_utilities.resolve_tool", fake_resolve_tool)

    result = ToolEnvironmentCheckSkill().run(
        SkillContext(tmp_path / "work", []),
        {"tools": ["multiqc", "seqkit", "gzip"]},
    )

    assert result.status == "dependency_missing"
    assert result.metrics["missing_tools"] == ["multiqc", "seqkit"]
    assert result.metrics["available_tools"] == ["gzip"]


def test_sample_sheet_validate_checks_columns_and_paths(tmp_path):
    read = tmp_path / "reads.fastq.gz"
    read.write_text("", encoding="utf-8")
    sheet = tmp_path / "samples.csv"
    sheet.write_text(
        f"sample_id,fastq_1,fastq_2\nS1,{read},\n",
        encoding="utf-8",
    )

    result = SampleSheetValidateSkill().run(SkillContext(tmp_path / "work", [sheet]), {})

    assert result.status == "succeeded"
    assert result.metrics["samples"] == 1
    assert result.warnings == []


def test_multiqc_summary_reports_missing_multiqc(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.workflow_utilities.resolve_tool",
        lambda names: None,
    )

    result = MultiqcSummarySkill().run(SkillContext(tmp_path / "work", [tmp_path]), {})

    assert result.status == "dependency_missing"
    assert "MultiQC" in result.error

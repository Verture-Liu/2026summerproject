import gzip
import json
from pathlib import Path

import pandas as pd

from research_agent.skills.base import SkillContext
from research_agent.skills.workflow_utilities import DataQualityGateSkill


def test_data_quality_gate_flags_invalid_duplicate_peptide_csv(tmp_path):
    source = tmp_path / "peptides.csv"
    pd.DataFrame(
        [
            {"label": 1, "sequence": "ACDEFGHIKLM"},
            {"label": 0, "sequence": "ACDEFGHIKLM"},
            {"label": 1, "sequence": "ACDZX"},
        ]
    ).to_csv(source, index=False)

    result = DataQualityGateSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"sequence_column": "sequence", "label_column": "label"},
    )

    assert result.status == "succeeded"
    assert result.metrics["gate_passed"] is False
    assert any("invalid amino acid" in warning for warning in result.warnings)
    assert any("duplicate sequence" in warning for warning in result.warnings)
    report = json.loads(Path(result.outputs[0]).read_text(encoding="utf-8"))
    assert report["files"][0]["rows"] == 3
    assert report["files"][0]["duplicate_sequences"] == 1


def test_data_quality_gate_passes_clean_peptide_csv(tmp_path):
    source = tmp_path / "peptides.csv"
    pd.DataFrame(
        [
            {"label": 1, "sequence": "ACDEFGHIKLM"},
            {"label": 0, "sequence": "LMNPQRSTVWY"},
        ]
    ).to_csv(source, index=False)

    result = DataQualityGateSkill().run(SkillContext(tmp_path / "work", [source]), {})

    assert result.status == "succeeded"
    assert result.metrics["gate_passed"] is True
    assert result.warnings == []


def test_data_quality_gate_does_not_fail_workflow_for_duplicate_only_warning(tmp_path):
    source = tmp_path / "peptides.csv"
    pd.DataFrame(
        [
            {"label": 1, "sequence": "ACDEFGHIKLM"},
            {"label": 0, "sequence": "ACDEFGHIKLM"},
        ]
    ).to_csv(source, index=False)

    result = DataQualityGateSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"sequence_column": "sequence", "label_column": "label", "fail_on_error": True},
    )

    assert result.status == "succeeded"
    assert result.metrics["gate_passed"] is False
    assert any("duplicate sequence" in warning for warning in result.warnings)


def test_data_quality_gate_still_fails_for_invalid_sequences_when_requested(tmp_path):
    source = tmp_path / "peptides.csv"
    pd.DataFrame([{"label": 1, "sequence": "ACDZX"}]).to_csv(source, index=False)

    result = DataQualityGateSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"sequence_column": "sequence", "label_column": "label", "fail_on_error": True},
    )

    assert result.status == "failed"
    assert "invalid amino acid" in result.error


def test_data_quality_gate_flags_paired_fastq_count_mismatch(tmp_path):
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    with gzip.open(r1, "wt", encoding="utf-8") as handle:
        handle.write("@r1\nACGT\n+\n!!!!\n@r2\nACGT\n+\n!!!!\n")
    with gzip.open(r2, "wt", encoding="utf-8") as handle:
        handle.write("@r1\nACGT\n+\n!!!!\n")

    result = DataQualityGateSkill().run(SkillContext(tmp_path / "work", [r1, r2]), {})

    assert result.status == "succeeded"
    assert result.metrics["gate_passed"] is False
    assert any("paired FASTQ read counts differ" in warning for warning in result.warnings)

import pandas as pd
import pytest

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.deduplicate import PeptideDeduplicateSkill
from tests.unit.peptide_table_helpers import write_table


def test_removes_same_label_duplicates_and_reports_them(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "ACDE"},
            {"label": 1, "sequence": "ACDE"},
            {"label": 0, "sequence": "LMNP"},
        ],
    )
    result = PeptideDeduplicateSkill().run(
        SkillContext(tmp_path / "work", [source]), {}
    )
    assert pd.read_csv(result.outputs[0])["sequence"].tolist() == ["ACDE", "LMNP"]
    assert result.metrics["duplicate_rows_removed"] == 1
    assert pd.read_csv(result.outputs[1]).iloc[0]["resolution"] == "duplicate_removed"


def test_conflicting_labels_fail_by_default_and_can_prefer_positive(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 0, "sequence": "ACDE"},
            {"label": 1, "sequence": "ACDE"},
        ],
    )
    with pytest.raises(ValueError, match="conflicting labels"):
        PeptideDeduplicateSkill().run(SkillContext(tmp_path / "fail", [source]), {})
    result = PeptideDeduplicateSkill().run(
        SkillContext(tmp_path / "positive", [source]),
        {"conflict_policy": "prefer_positive"},
    )
    assert pd.read_csv(result.outputs[0]).iloc[0]["label"] == 1

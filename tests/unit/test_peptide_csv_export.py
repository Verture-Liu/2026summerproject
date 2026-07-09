import pandas as pd
import pytest

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.export import PeptideCsvExportSkill
from tests.unit.peptide_table_helpers import write_table


def test_exports_selected_columns_with_stable_sort(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 0, "sequence": "ZZZ"},
            {"label": 1, "sequence": "AAA"},
        ],
    )
    result = PeptideCsvExportSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {
            "columns": ["sequence", "label"],
            "sort_by": "sequence",
            "filename": "final.csv",
        },
    )
    frame = pd.read_csv(result.outputs[0])
    assert list(frame.columns) == ["sequence", "label"]
    assert frame["sequence"].tolist() == ["AAA", "ZZZ"]


def test_star_columns_exports_all_columns(tmp_path):
    source = write_table(tmp_path, [{"label": 1, "sequence": "ACDE"}])

    result = PeptideCsvExportSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"columns": ["*"], "filename": "cleaned_peptides.csv"},
    )

    frame = pd.read_csv(result.outputs[0])
    assert list(frame.columns) == ["label", "sequence"]
    assert result.metrics["columns"] == ["label", "sequence"]


@pytest.mark.parametrize("filename", ["../escape.csv", "/tmp/escape.csv", "bad.txt"])
def test_rejects_unsafe_filenames(tmp_path, filename):
    source = write_table(tmp_path, [{"label": 1, "sequence": "ACDE"}])
    with pytest.raises(ValueError, match="filename"):
        PeptideCsvExportSkill().run(
            SkillContext(tmp_path / "work", [source]), {"filename": filename}
        )

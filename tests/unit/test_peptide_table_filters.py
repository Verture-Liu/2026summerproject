from pathlib import Path

import pandas as pd

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.filters import (
    PeptideLabelFilterSkill,
    PeptideLengthFilterSkill,
)
from tests.unit.peptide_table_helpers import write_table


def test_filters_positive_peptides_with_inclusive_length_bounds(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "A" * 13},
            {"label": 1, "sequence": "A" * 26},
            {"label": 1, "sequence": "A" * 27},
            {"label": 0, "sequence": "A" * 20},
        ],
    )
    labels = PeptideLabelFilterSkill().run(
        SkillContext(tmp_path / "labels", [source]), {"labels": [1]}
    )
    lengths = PeptideLengthFilterSkill().run(
        SkillContext(tmp_path / "length", [Path(labels.outputs[0])]),
        {"min_length": 13, "max_length": 26},
    )
    frame = pd.read_csv(lengths.outputs[0])
    assert frame["length"].tolist() == [13, 26]


def test_empty_filter_result_succeeds_with_warning(tmp_path):
    source = write_table(tmp_path, [{"label": 0, "sequence": "ACDE"}])
    result = PeptideLabelFilterSkill().run(
        SkillContext(tmp_path / "work", [source]), {"labels": [1]}
    )
    assert result.status == "succeeded"
    assert result.warnings == ["No rows matched the filter."]

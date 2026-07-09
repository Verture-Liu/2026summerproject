import json

import pandas as pd

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.statistics import PeptideStatisticsSkill
from tests.unit.peptide_table_helpers import write_table


def test_calculates_descriptive_statistics_and_composition(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "AAA"},
            {"label": 1, "sequence": "ACD"},
            {"label": 0, "sequence": "GGG"},
        ],
    )
    result = PeptideStatisticsSkill().run(
        SkillContext(tmp_path / "work", [source]), {}
    )
    stats = json.loads(open(result.outputs[0], encoding="utf-8").read())
    assert stats["total_rows"] == 3
    assert stats["unique_sequences"] == 3
    assert stats["label_counts"] == {"0": 1, "1": 2}
    assert stats["length"]["mean"] == 3.0
    composition = pd.read_csv(result.outputs[2]).set_index("amino_acid")
    assert composition.loc["A", "count"] == 4

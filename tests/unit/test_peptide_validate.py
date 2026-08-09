import pandas as pd
import pytest

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.validate import PeptideValidateSkill
from tests.unit.peptide_table_helpers import write_table


def test_rejects_invalid_amino_acids_empty_and_out_of_range_sequences(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "ACDEFG"},
            {"label": 0, "sequence": "ACDZ"},
            {"label": 1, "sequence": ""},
            {"label": 1, "sequence": "A"},
        ],
    )
    result = PeptideValidateSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"min_length": 2, "invalid_row_policy": "reject"},
    )
    assert result.metrics["valid_rows"] == 1
    rejected = pd.read_csv(result.outputs[1])
    assert result.named_outputs["validated_csv"] == result.outputs[0]
    assert result.named_outputs["rejected_csv"] == result.outputs[1]
    assert set(rejected["rejection_reason"]) == {
        "invalid_amino_acid",
        "empty_sequence",
        "below_min_length",
    }


def test_fail_policy_raises_before_returning_outputs(tmp_path):
    source = write_table(tmp_path, [{"label": 1, "sequence": "ACDZ"}])
    with pytest.raises(ValueError, match="1 invalid peptide row"):
        PeptideValidateSkill().run(
            SkillContext(tmp_path / "work", [source]),
            {"invalid_row_policy": "fail"},
        )

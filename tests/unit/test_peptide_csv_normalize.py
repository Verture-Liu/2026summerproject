from pathlib import Path

import pandas as pd
import pytest

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.normalize import PeptideCsvNormalizeSkill


def run_skill(tmp_path: Path, text: str, parameters=None, suffix=".csv"):
    source = tmp_path / f"input{suffix}"
    source.write_text(text, encoding="utf-8")
    return PeptideCsvNormalizeSkill().run(
        SkillContext(tmp_path / "work", [source]), parameters or {}
    )


def test_normalizes_headerless_amplit_csv(tmp_path):
    result = run_skill(tmp_path, "1,ACDEFG\n0,LMNPQR\n")
    frame = pd.read_csv(result.outputs[0])
    assert frame.to_dict("records") == [
        {"label": 1, "sequence": "ACDEFG"},
        {"label": 0, "sequence": "LMNPQR"},
    ]
    assert result.metrics["header_detected"] is False


def test_headerless_csv_ignores_row_values_misplanned_as_column_names(tmp_path):
    result = run_skill(
        tmp_path,
        "1,GIGAVLKVLTTGLPALISWISRKKRQQ\n0,LMNPQR\n",
        {
            "label_column": "1",
            "sequence_column": "GIGAVLKVLTTGLPALISWISRKKRQQ",
            "drop_empty_rows": True,
        },
    )

    frame = pd.read_csv(result.outputs[0])

    assert frame.to_dict("records") == [
        {"label": 1, "sequence": "GIGAVLKVLTTGLPALISWISRKKRQQ"},
        {"label": 0, "sequence": "LMNPQR"},
    ]
    assert result.metrics["header_detected"] is False
    assert result.metrics["label_column"] == "0"
    assert result.metrics["sequence_column"] == "1"
    assert result.warnings == [
        "Headerless peptide table received non-index column hints; using columns 0 and 1."
    ]


def test_normalizes_named_columns_boolean_labels_and_lowercase(tmp_path):
    result = run_skill(tmp_path, "class,peptide\ntrue, acdefg \nfalse,lmn\n")
    frame = pd.read_csv(result.outputs[0])
    assert frame.to_dict("records") == [
        {"label": 1, "sequence": "ACDEFG"},
        {"label": 0, "sequence": "LMN"},
    ]
    assert result.metrics["header_detected"] is True


def test_auto_detects_tsv_and_explicit_column_indices(tmp_path):
    result = run_skill(
        tmp_path,
        "name\tsequence\tlabel\nx\tacde\t1\n",
        {"label_column": 2, "sequence_column": 1},
        ".tsv",
    )
    assert pd.read_csv(result.outputs[0]).iloc[0].to_dict() == {
        "label": 1,
        "sequence": "ACDE",
    }


def test_rejects_non_binary_labels(tmp_path):
    with pytest.raises(ValueError, match="binary"):
        run_skill(tmp_path, "2,ACDE\n")

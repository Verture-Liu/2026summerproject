import json
import os
from pathlib import Path

import pandas as pd

from research_agent.skills.amplit.skill import AmplitPredictionSkill
from research_agent.skills.base import SkillContext


REQUIRED_FILES = [
    "utils1.py",
    "word2vec11.bin",
    "Model/G1.h5",
    "Model/G2.h5",
    "Model/G3.h5",
]


def write_input(tmp_path: Path) -> Path:
    source = tmp_path / "peptides.csv"
    pd.DataFrame(
        [
            {"label": 1, "sequence": "ACDEFGHIKLM"},
            {"label": 0, "sequence": "LMNPQRSTVWY"},
        ]
    ).to_csv(source, index=False)
    return source


def make_fake_amplit_environment(tmp_path: Path) -> tuple[Path, Path]:
    home = tmp_path / "AMPLiT"
    for relative in REQUIRED_FILES:
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"official-test-resource")
    python_executable = tmp_path / "fake-amplit-python"
    python_executable.write_text(
        """#!/usr/bin/env python3
import csv
import json
import sys

if sys.argv[1] == "-c":
    print(json.dumps({
        "python_version": "3.9.7",
        "imports": {
            "keras": True,
            "pandas": True,
            "numpy": True,
            "sklearn": True,
            "propy": True,
            "gensim": True,
            "scipy": True,
            "tensorflow": True,
            "torch": True
        }
    }))
    raise SystemExit(0)

args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
with open(args["--input"], newline="", encoding="utf-8") as source:
    rows = list(csv.DictReader(source))
with open(args["--output"], "w", newline="", encoding="utf-8") as target:
    writer = csv.DictWriter(target, fieldnames=["row_id", "sequence", "amp_score"])
    writer.writeheader()
    for index, row in enumerate(rows):
        writer.writerow({
            "row_id": row["row_id"],
            "sequence": row["sequence"],
            "amp_score": 0.9 if index == 0 else 0.2
        })
""",
        encoding="utf-8",
    )
    python_executable.chmod(0o755)
    return home, python_executable


def test_missing_environment_returns_actionable_dependency_report(tmp_path):
    skill = AmplitPredictionSkill(env={})
    result = skill.run(
        SkillContext(tmp_path / "work", [write_input(tmp_path)]),
        {"score_threshold": 0.5},
    )
    assert result.status == "dependency_missing"
    assert "AMPLIT_HOME" in result.error
    assert "AMPLIT_PYTHON" in result.error
    assert "github.com/ChenSizhe13893461199/AMPLiT" in result.error
    assert result.outputs == []


def test_ready_environment_runs_prediction_and_validates_output(tmp_path):
    home, python_executable = make_fake_amplit_environment(tmp_path)
    skill = AmplitPredictionSkill(
        env={
            "AMPLIT_HOME": str(home),
            "AMPLIT_PYTHON": str(python_executable),
        }
    )
    result = skill.run(
        SkillContext(tmp_path / "work", [write_input(tmp_path)]),
        {"score_threshold": 0.5},
    )
    assert result.status == "succeeded"
    frame = pd.read_csv(result.outputs[0])
    assert frame.to_dict("records") == [
        {
            "label": 1,
            "sequence": "ACDEFGHIKLM",
            "amp_score": 0.9,
            "predicted_label": 1,
        },
        {
            "label": 0,
            "sequence": "LMNPQRSTVWY",
            "amp_score": 0.2,
            "predicted_label": 0,
        },
    ]
    metadata = json.loads(Path(result.outputs[1]).read_text(encoding="utf-8"))
    assert metadata["model_files"] == ["G1.h5", "G2.h5", "G3.h5"]
    assert metadata["input_rows"] == 2


def test_dependency_check_rejects_missing_model_file(tmp_path):
    home, python_executable = make_fake_amplit_environment(tmp_path)
    (home / "Model" / "G2.h5").unlink()
    skill = AmplitPredictionSkill(
        env={
            "AMPLIT_HOME": str(home),
            "AMPLIT_PYTHON": str(python_executable),
        }
    )
    report = skill.check_dependencies(tmp_path / "work")
    assert report["ready"] is False
    assert any("Model/G2.h5" in item for item in report["missing"])


def test_rejects_scores_outside_zero_to_one(tmp_path):
    home, python_executable = make_fake_amplit_environment(tmp_path)
    text = python_executable.read_text(encoding="utf-8").replace(
        "0.9 if index == 0 else 0.2", "1.5"
    )
    python_executable.write_text(text, encoding="utf-8")
    python_executable.chmod(0o755)
    result = AmplitPredictionSkill(
        env={
            "AMPLIT_HOME": str(home),
            "AMPLIT_PYTHON": str(python_executable),
        }
    ).run(
        SkillContext(tmp_path / "work", [write_input(tmp_path)]),
        {"score_threshold": 0.5},
    )
    assert result.status == "failed"
    assert "0 and 1" in result.error


def test_rejects_sequences_shorter_than_official_input_range(tmp_path):
    home, python_executable = make_fake_amplit_environment(tmp_path)
    source = tmp_path / "short.csv"
    pd.DataFrame([{"sequence": "ACDEFGHIK"}]).to_csv(source, index=False)
    result = AmplitPredictionSkill(
        env={
            "AMPLIT_HOME": str(home),
            "AMPLIT_PYTHON": str(python_executable),
        }
    ).run(
        SkillContext(tmp_path / "work", [source]),
        {"score_threshold": 0.5},
    )
    assert result.status == "failed"
    assert "11 and 50" in result.error


def test_rejects_output_sequence_mismatch(tmp_path):
    home, python_executable = make_fake_amplit_environment(tmp_path)
    text = python_executable.read_text(encoding="utf-8").replace(
        '"sequence": row["sequence"]', '"sequence": "AAAAAAAAAAA"'
    )
    python_executable.write_text(text, encoding="utf-8")
    python_executable.chmod(0o755)
    result = AmplitPredictionSkill(
        env={
            "AMPLIT_HOME": str(home),
            "AMPLIT_PYTHON": str(python_executable),
        }
    ).run(
        SkillContext(tmp_path / "work", [write_input(tmp_path)]),
        {"score_threshold": 0.5},
    )
    assert result.status == "failed"
    assert "sequences do not match" in result.error

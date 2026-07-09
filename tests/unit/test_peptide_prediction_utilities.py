from pathlib import Path

import pandas as pd

from research_agent.skills.amplit.external_predictors import (
    AmplifyPredictionSkill,
    AmpScannerPredictionSkill,
    ModlampDescriptorSkill,
)
from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.prediction_utilities import (
    PeptideCandidateRankSkill,
    PeptidePropertiesSkill,
)


def test_peptide_properties_calculates_basic_descriptors(tmp_path):
    source = tmp_path / "peptides.csv"
    pd.DataFrame([{"sequence": "AKK"}, {"sequence": "DD"}]).to_csv(source, index=False)

    result = PeptidePropertiesSkill().run(SkillContext(tmp_path / "work", [source]), {})

    assert result.status == "succeeded"
    frame = pd.read_csv(result.outputs[0])
    assert list(frame["length"]) == [3, 2]
    assert list(frame["net_charge"]) == [2, -2]
    assert "molecular_weight" in frame.columns
    assert "hydrophobic_fraction" in frame.columns


def test_peptide_candidate_rank_combines_prediction_scores(tmp_path):
    source = tmp_path / "predictions.csv"
    pd.DataFrame(
        [
            {"sequence": "AAA", "amp_score": 0.8, "toxicity_score": 0.1},
            {"sequence": "KKK", "amp_score": 0.7, "toxicity_score": 0.8},
        ]
    ).to_csv(source, index=False)

    result = PeptideCandidateRankSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {
            "positive_score_columns": ["amp_score"],
            "negative_score_columns": ["toxicity_score"],
        },
    )

    assert result.status == "succeeded"
    frame = pd.read_csv(result.outputs[0])
    assert frame.iloc[0]["sequence"] == "AAA"
    assert frame.iloc[0]["candidate_rank"] == 1


def test_external_amp_predictors_report_missing_environment(tmp_path, monkeypatch):
    source = tmp_path / "peptides.fasta"
    source.write_text(">p1\nACDEFGHIKLM\n", encoding="utf-8")
    monkeypatch.setattr(
        "research_agent.skills.amplit.external_predictors.shutil.which",
        lambda name: None,
    )

    for skill in (AmplifyPredictionSkill(), AmpScannerPredictionSkill(), ModlampDescriptorSkill()):
        result = skill.run(SkillContext(tmp_path / skill.name, [source]), {})
        assert result.status == "dependency_missing"
        assert skill.executable_candidates[0] in result.error

from pathlib import Path

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_filter.skill import PeptideFilterSkill


def test_peptide_filter_keeps_requested_lengths(tmp_path):
    source = tmp_path / "input.fasta"
    source.write_text(">a\nAAAAAAAAAAAAA\n>b\nAAAA\n", encoding="utf-8")
    result = PeptideFilterSkill().run(
        SkillContext(tmp_path, [source]),
        {"min_length": 13, "max_length": 26},
    )
    assert result.metrics["kept"] == 1
    assert Path(result.outputs[0]).read_text(encoding="utf-8").startswith(">a")

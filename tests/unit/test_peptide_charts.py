from pathlib import Path
import os
import subprocess
import sys

import pytest

from research_agent.skills.base import SkillContext
from research_agent.skills.peptide_table.charts import PeptideChartSkill
from tests.unit.peptide_table_helpers import write_table


def test_generates_requested_png_charts(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "ACDE"},
            {"label": 0, "sequence": "AAAAAA"},
        ],
    )
    result = PeptideChartSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"charts": ["length_histogram", "label_counts", "amino_acid_composition"]},
    )
    assert len(result.outputs) == 3
    for output in result.outputs:
        assert Path(output).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_accepts_length_distribution_alias_for_length_histogram(tmp_path):
    source = write_table(
        tmp_path,
        [
            {"label": 1, "sequence": "ACDE"},
            {"label": 0, "sequence": "AAAAAA"},
        ],
    )
    result = PeptideChartSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"charts": ["length_distribution", "label_distribution"]},
    )
    assert [Path(output).name for output in result.outputs] == [
        "length_histogram.png",
        "label_counts.png",
    ]


def test_chart_rejects_empty_input(tmp_path):
    source = write_table(tmp_path, [])
    with pytest.raises(ValueError, match="empty"):
        PeptideChartSkill().run(
            SkillContext(tmp_path / "work", [source]),
            {"charts": ["label_counts"]},
        )


def test_chart_module_uses_writable_cache_when_home_is_unavailable(tmp_path):
    environment = os.environ.copy()
    environment["HOME"] = str(tmp_path / "missing-home")
    environment.pop("MPLCONFIGDIR", None)
    environment.pop("XDG_CACHE_HOME", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; "
                "import research_agent.skills.peptide_table.charts; "
                "print(os.environ.get('MPLCONFIGDIR', '')); "
                "print(os.environ.get('XDG_CACHE_HOME', ''))"
            ),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    cache_lines = completed.stdout.splitlines()
    assert len(cache_lines) >= 2
    assert cache_lines[-2]
    assert cache_lines[-1]
    assert "not a writable directory" not in completed.stderr
    assert "No writable cache directories" not in completed.stderr

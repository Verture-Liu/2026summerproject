from pathlib import Path

from analysis.benchmark_multimodel.run_cross_model import experiment_check
from analysis.benchmark_v2.config import BenchmarkConfig


ROOT = Path(__file__).resolve().parents[2]


def test_cross_model_check_is_fixed_and_isolated():
    config = BenchmarkConfig("https://api.deepseek.com", "secret", "deepseek-v4-pro", 120, 2)
    report = experiment_check(
        ROOT,
        ROOT / "analysis/benchmark_v5/heldout_manifest.json",
        ROOT / "analysis/benchmark_multimodel/v4_pro/runs",
        config,
    )
    assert report["ok"] is True
    assert report["model"] == "deepseek-v4-pro"
    assert report["scenario_count"] == 8
    assert report["repeats"] == 3
    assert report["formal_calls"] == 48
    assert report["runs_directory"].endswith("analysis/benchmark_multimodel/v4_pro/runs")
    assert "secret" not in str(report)

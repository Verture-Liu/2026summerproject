import json

from analysis.benchmark_v2.io_utils import atomic_write_json, bundle_is_complete
from analysis.benchmark_v2.summary import exact_mcnemar, summarize_records


def test_atomic_bundle_completion_requires_marker(tmp_path):
    bundle = tmp_path / "run"
    atomic_write_json(bundle / "score.json", {"strict_success": True})
    assert bundle_is_complete(bundle) is False
    atomic_write_json(bundle / "complete.json", {"complete": True})
    assert bundle_is_complete(bundle) is True


def test_summary_preserves_pairs_and_computes_exact_mcnemar():
    records = [
        {"scenario_id": "A", "repeat": 1, "arm": "raw_llm", "strict_success": False},
        {"scenario_id": "A", "repeat": 1, "arm": "paleorigor", "strict_success": True},
        {"scenario_id": "B", "repeat": 1, "arm": "raw_llm", "strict_success": True},
        {"scenario_id": "B", "repeat": 1, "arm": "paleorigor", "strict_success": True},
    ]
    result = summarize_records(records)
    assert result["pairs"] == 2
    assert result["discordant"]["paleorigor_only"] == 1
    assert result["discordant"]["raw_only"] == 0
    assert result["mcnemar_exact_two_sided_p"] == exact_mcnemar(1, 0) == 1.0
    assert result["by_scenario"]["A"]["paleorigor"]["rate"] == 1.0
    assert result["by_scenario"]["A"]["raw_llm"]["rate"] == 0.0

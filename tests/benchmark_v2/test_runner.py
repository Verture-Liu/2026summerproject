import json
from pathlib import Path

from analysis.benchmark_v2.client import Completion
from analysis.benchmark_v2.config import BenchmarkConfig
from analysis.benchmark_v2.run_benchmark import run_one
from analysis.benchmark_v2.scenarios import load_scenarios


ROOT = Path(__file__).resolve().parents[2]


class FakeClient:
    def complete(self, messages):
        return Completion(
            content=json.dumps({"status": "blocked", "reason_code": "file_type_mismatch", "message": "CSV is not FASTQ"}),
            model="deepseek-v4-flash",
            usage={"total_tokens": 12},
            latency_seconds=0.01,
            attempts=1,
        )


def test_runner_writes_redacted_complete_boundary_bundle(tmp_path):
    config = BenchmarkConfig("https://api.deepseek.com", "never-write-me", "deepseek-v4-flash", 30, 0)
    scenario = load_scenarios(ROOT)[2]
    bundle = run_one(ROOT, tmp_path, config, FakeClient(), scenario, 1, "paleorigor")
    assert (bundle / "complete.json").is_file()
    assert json.loads((bundle / "score.json").read_text())["strict_success"] is True
    combined = "".join(path.read_text(errors="ignore") for path in bundle.rglob("*") if path.is_file())
    assert "never-write-me" not in combined
    assert not (bundle / "execution.json").exists()

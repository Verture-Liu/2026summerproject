from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.benchmark_v2.io_utils import atomic_write_json
from analysis.benchmark_v2.summary import summarize_records


def collect_records(runs_root: Path) -> list[dict]:
    records = []
    for score_path in sorted(Path(runs_root).glob("*/repeat_*/*/score.json")):
        bundle = score_path.parent
        score = json.loads(score_path.read_text(encoding="utf-8"))
        provenance_path = bundle / "provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
        records.append(
            {
                "scenario_id": bundle.parents[1].name,
                "repeat": int(bundle.parent.name.split("_")[-1]),
                "arm": bundle.name,
                "strict_success": bool(score.get("strict_success")),
                "decision": score.get("decision"),
                "failure_codes": ";".join(score.get("failure_codes", [])),
                "latency_seconds": provenance.get("latency_seconds", ""),
                "total_tokens": provenance.get("usage", {}).get("total_tokens", ""),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", default="analysis/benchmark_v2/runs")
    parser.add_argument("--results-root", default="analysis/benchmark_v2/results")
    args = parser.parse_args()
    output = (PROJECT_ROOT / args.results_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = collect_records((PROJECT_ROOT / args.runs_root).resolve())
    fields = ["scenario_id", "repeat", "arm", "strict_success", "decision", "failure_codes", "latency_seconds", "total_tokens"]
    with (output / "run_level.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    summary = summarize_records(records)
    atomic_write_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

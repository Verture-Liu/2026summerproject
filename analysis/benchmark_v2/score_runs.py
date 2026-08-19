from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in [PROJECT_ROOT, PROJECT_ROOT / "src"]:
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from analysis.benchmark_v2.scenarios import load_scenarios
from analysis.benchmark_v2.scoring import score_completion


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--runs-root", default="analysis/benchmark_v2/runs")
    args = parser.parse_args()
    manifest = (PROJECT_ROOT / args.manifest).resolve() if args.manifest else None
    scenarios = {item.id: item for item in load_scenarios(PROJECT_ROOT, manifest_path=manifest)}
    runs_root = (PROJECT_ROOT / args.runs_root).resolve()
    checked = 0
    discrepancies = []
    for bundle in sorted(path.parent for path in runs_root.glob("*/repeat_*/*/score.json")):
        scenario_id = bundle.parents[1].name
        content_path = bundle / ("repair_completion.txt" if (bundle / "repair_completion.txt").exists() else "raw_completion.txt")
        if not content_path.exists():
            continue
        fresh = score_completion(content_path.read_text(encoding="utf-8"), scenarios[scenario_id]).to_dict()
        execution_path = bundle / "execution.json"
        if execution_path.exists() and json.loads(execution_path.read_text(encoding="utf-8"))["status"] != "succeeded":
            fresh["strict_success"] = False
            fresh["failure_codes"] = list(fresh["failure_codes"]) + ["execution_failed"]
        stored = json.loads((bundle / "score.json").read_text(encoding="utf-8"))
        checked += 1
        for field in ["strict_success", "decision", "failure_codes"]:
            fresh_value = list(fresh[field]) if field == "failure_codes" else fresh[field]
            stored_value = list(stored[field]) if field == "failure_codes" else stored[field]
            if fresh_value != stored_value:
                discrepancies.append({"bundle": str(bundle.relative_to(PROJECT_ROOT)), "field": field, "stored": stored[field], "fresh": fresh[field]})
    result = {"checked": checked, "discrepancies": discrepancies, "all_match": not discrepancies}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not discrepancies else 1


if __name__ == "__main__":
    raise SystemExit(main())

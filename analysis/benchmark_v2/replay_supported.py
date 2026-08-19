from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in [PROJECT_ROOT, PROJECT_ROOT / "src"]:
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from analysis.benchmark_v2.io_utils import atomic_write_json
from analysis.benchmark_v2.scenarios import load_scenarios
from analysis.benchmark_v2.scoring import score_completion
from research_agent.agent.models import Workflow
from research_agent.execution.executor import execute_workflow
from research_agent.skills.registry import build_default_registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--runs-root", default="analysis/benchmark_v2/runs")
    parser.add_argument(
        "--output-root",
        default="analysis/benchmark_v2/development_runs/round_01_contract_replay",
    )
    parser.add_argument("--scenario", action="append")
    args = parser.parse_args()
    formal_root = (PROJECT_ROOT / args.runs_root).resolve()
    output_root = (PROJECT_ROOT / args.output_root).resolve()
    manifest = (PROJECT_ROOT / args.manifest).resolve() if args.manifest else None
    scenarios = {
        item.id: item
        for item in load_scenarios(PROJECT_ROOT, manifest_path=manifest)
        if item.kind == "supported"
    }
    if args.scenario:
        requested = set(args.scenario)
        unknown = requested - set(scenarios)
        if unknown:
            parser.error(f"Unknown supported scenario(s): {', '.join(sorted(unknown))}")
        scenarios = {key: value for key, value in scenarios.items() if key in requested}
    records = []
    for scenario_id, scenario in scenarios.items():
        for repeat in range(1, 4):
            for arm in ["raw_llm", "paleorigor"]:
                source_bundle = formal_root / scenario_id / f"repeat_{repeat:02d}" / arm
                completion_path = source_bundle / (
                    "repair_completion.txt" if (source_bundle / "repair_completion.txt").exists() else "raw_completion.txt"
                )
                score = score_completion(completion_path.read_text(encoding="utf-8"), scenario)
                execution_status = "not_run"
                if score.strict_success and score.workflow is not None:
                    task_dir = output_root / scenario_id / f"repeat_{repeat:02d}" / arm
                    if task_dir.exists():
                        shutil.rmtree(task_dir)
                    execution = execute_workflow(
                        Workflow.model_validate(score.workflow),
                        task_dir,
                        dict(zip(scenario.input_refs, scenario.input_paths)),
                        build_default_registry(),
                        {},
                    )
                    execution_status = execution.status
                records.append(
                    {
                        "scenario_id": scenario_id,
                        "repeat": repeat,
                        "arm": arm,
                        "planning_contract_passed": score.strict_success,
                        "execution_status": execution_status,
                        "development_success": score.strict_success and execution_status == "succeeded",
                    }
                )
    result = {
        "purpose": "development regression replay; not a confirmatory benchmark",
        "records": records,
        "paleorigor": {
            "successes": sum(item["development_success"] for item in records if item["arm"] == "paleorigor"),
            "total": sum(item["arm"] == "paleorigor" for item in records),
        },
        "raw_llm": {
            "successes": sum(item["development_success"] for item in records if item["arm"] == "raw_llm"),
            "total": sum(item["arm"] == "raw_llm" for item in records),
        },
    }
    atomic_write_json(output_root / "replay_summary.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

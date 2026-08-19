from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in [PROJECT_ROOT, PROJECT_ROOT / "src"]:
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from analysis.benchmark_v2.client import DeepSeekClient
from analysis.benchmark_v2.config import BenchmarkConfig, load_config_for_model
from analysis.benchmark_v2.io_utils import atomic_write_json
from analysis.benchmark_v2.run_benchmark import run_one
from analysis.benchmark_v2.scenarios import build_call_schedule, load_scenarios


FROZEN_MANIFEST = PROJECT_ROOT / "analysis" / "benchmark_v5" / "heldout_manifest.json"
DEFAULT_MODEL = "deepseek-v4-pro"


def experiment_check(
    project_root: Path,
    manifest_path: Path,
    runs_root: Path,
    config: BenchmarkConfig,
) -> dict:
    scenarios = load_scenarios(project_root, manifest_path=manifest_path)
    missing = [str(path) for scenario in scenarios for path in scenario.input_paths if not path.is_file()]
    schedule = build_call_schedule(scenarios, repeats=3)
    return {
        "ok": not missing and len(scenarios) == 8 and len(schedule) == 24,
        "missing_inputs": missing,
        "model": config.model,
        "scenario_count": len(scenarios),
        "repeats": 3,
        "formal_calls": len(schedule) * 2,
        "config": config.redacted(),
        "manifest": str(manifest_path),
        "runs_directory": str(runs_root),
    }


def health_check(config: BenchmarkConfig, output: Path) -> dict:
    with httpx.Client(verify=True) as http:
        client = DeepSeekClient(
            http,
            config.base_url,
            config.api_key,
            config.model,
            config.timeout_seconds,
            config.max_retries,
        )
        completion = client.complete(
            [
                {"role": "system", "content": "Return exactly one JSON object."},
                {"role": "user", "content": 'Return {"status":"ok"}.'},
            ]
        )
    record = {
        "excluded_from_formal_sample": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "requested_model": config.model,
        "model_reported": completion.model,
        "usage": completion.usage,
        "latency_seconds": completion.latency_seconds,
        "attempts": completion.attempts,
        "response_is_json": isinstance(json.loads(completion.content), dict),
        "config": config.redacted(),
    }
    atomic_write_json(output, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen v5 benchmark on a preregistered V4 model.")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=["deepseek-v4-pro"])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-execute", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--arm", choices=["raw_llm", "paleorigor"])
    parser.add_argument("--scenario", action="append")
    args = parser.parse_args()

    config = load_config_for_model(PROJECT_ROOT / ".env", args.model)
    model_slug = args.model.replace("deepseek-", "").replace("-", "_")
    experiment_root = PROJECT_ROOT / "analysis" / "benchmark_multimodel" / model_slug
    runs_root = experiment_root / "runs"
    check = experiment_check(PROJECT_ROOT, FROZEN_MANIFEST, runs_root, config)
    if args.check:
        print(json.dumps(check, ensure_ascii=False, indent=2))
        return 0 if check["ok"] else 1
    if not check["ok"]:
        raise RuntimeError(f"Experiment check failed: {check}")
    if args.health_check:
        print(json.dumps(health_check(config, experiment_root / "health_check.json"), ensure_ascii=False, indent=2))
        return 0

    scenarios = load_scenarios(PROJECT_ROOT, manifest_path=FROZEN_MANIFEST)
    by_id = {scenario.id: scenario for scenario in scenarios}
    calls = [(pair, arm) for pair in build_call_schedule(scenarios, repeats=3) for arm in pair.arm_order]
    if args.arm:
        calls = [(pair, arm) for pair, arm in calls if arm == args.arm]
    if args.scenario:
        requested = set(args.scenario)
        unknown = requested - set(by_id)
        if unknown:
            parser.error(f"Unknown scenario(s): {', '.join(sorted(unknown))}")
        calls = [(pair, arm) for pair, arm in calls if pair.scenario_id in requested]
    if args.limit is not None:
        calls = calls[: args.limit]

    with httpx.Client(verify=True) as http:
        client = DeepSeekClient(
            http,
            config.base_url,
            config.api_key,
            config.model,
            config.timeout_seconds,
            config.max_retries,
        )
        for index, (pair, arm) in enumerate(calls, 1):
            print(f"[{index}/{len(calls)}] {pair.scenario_id} repeat={pair.repeat} arm={arm}", flush=True)
            run_one(
                PROJECT_ROOT,
                runs_root,
                config,
                client,
                by_id[pair.scenario_id],
                pair.repeat,
                arm,
                force=args.force,
                execute_supported=not args.no_execute,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

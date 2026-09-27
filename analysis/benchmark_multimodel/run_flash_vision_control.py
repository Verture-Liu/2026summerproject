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
from analysis.benchmark_v2.config import BenchmarkConfig, _parse_env
from analysis.benchmark_v2.io_utils import atomic_write_json
from analysis.benchmark_v2.run_benchmark import run_one
from analysis.benchmark_v2.scenarios import build_call_schedule, load_scenarios


CONTROL_MODEL = "deepseek-v4-flash-vision-exp"
FROZEN_MANIFEST = PROJECT_ROOT / "analysis" / "benchmark_v5" / "heldout_manifest.json"
EXPERIMENT_ROOT = PROJECT_ROOT / "analysis" / "benchmark_multimodel" / "v4_flash_vision_exp"


def load_experimental_config(path: Path) -> BenchmarkConfig:
    values = _parse_env(path)
    missing = [key for key in ["AGENT_API_BASE_URL", "AGENT_API_KEY"] if not values.get(key)]
    if missing:
        raise ValueError(f"Missing environment setting(s): {', '.join(missing)}")
    return BenchmarkConfig(
        base_url=values["AGENT_API_BASE_URL"].rstrip("/"),
        api_key=values["AGENT_API_KEY"],
        model=CONTROL_MODEL,
        timeout_seconds=float(values.get("AGENT_TIMEOUT_SECONDS", "120")),
        max_retries=int(values.get("AGENT_MAX_RETRIES", "2")),
    )


def require_exact_model(advertised_models: list[str], requested_model: str) -> None:
    if requested_model not in advertised_models:
        raise RuntimeError(f"Requested model {requested_model!r} is not advertised by the provider")


def provider_models(http: httpx.Client, config: BenchmarkConfig) -> list[str]:
    response = http.get(
        f"{config.base_url}/models",
        headers={"Authorization": f"Bearer {config.api_key}"},
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    return [item["id"] for item in response.json().get("data", []) if item.get("id")]


def build_experiment_check(
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
        "arm": "raw_llm",
        "scenario_count": len(scenarios),
        "repeats": 3,
        "formal_calls": len(schedule),
        "config": config.redacted(),
        "manifest": str(manifest_path),
        "runs_directory": str(runs_root),
        "comparison_target": "deepseek-v4-pro + PaleoRigor skills (previously completed)",
        "interpretation": "Exploratory cross-model comparison; model and control layer differ.",
    }


def health_check(config: BenchmarkConfig, output: Path) -> dict:
    with httpx.Client(verify=True) as http:
        advertised = provider_models(http, config)
        require_exact_model(advertised, config.model)
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
    if completion.model != config.model:
        raise RuntimeError(
            f"Provider reported {completion.model!r} for requested model {config.model!r}; refusing formal collection"
        )
    record = {
        "excluded_from_formal_sample": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "requested_model": config.model,
        "model_reported": completion.model,
        "advertised_models": advertised,
        "usage": completion.usage,
        "latency_seconds": completion.latency_seconds,
        "attempts": completion.attempts,
        "response_is_json": isinstance(json.loads(completion.content), dict),
        "config": config.redacted(),
    }
    atomic_write_json(output, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen 24-task raw-model control on DeepSeek V4 Flash Vision Exp."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-execute", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--scenario", action="append")
    args = parser.parse_args()

    config = load_experimental_config(PROJECT_ROOT / ".env")
    runs_root = EXPERIMENT_ROOT / "runs"
    check = build_experiment_check(PROJECT_ROOT, FROZEN_MANIFEST, runs_root, config)
    if args.check:
        print(json.dumps(check, ensure_ascii=False, indent=2))
        return 0 if check["ok"] else 1
    if not check["ok"]:
        raise RuntimeError(f"Experiment check failed: {check}")
    if args.health_check:
        print(json.dumps(health_check(config, EXPERIMENT_ROOT / "health_check.json"), ensure_ascii=False, indent=2))
        return 0

    scenarios = load_scenarios(PROJECT_ROOT, manifest_path=FROZEN_MANIFEST)
    by_id = {scenario.id: scenario for scenario in scenarios}
    calls = build_call_schedule(scenarios, repeats=3)
    if args.scenario:
        requested = set(args.scenario)
        unknown = requested - set(by_id)
        if unknown:
            parser.error(f"Unknown scenario(s): {', '.join(sorted(unknown))}")
        calls = [pair for pair in calls if pair.scenario_id in requested]
    if args.limit is not None:
        calls = calls[: args.limit]

    with httpx.Client(verify=True) as http:
        advertised = provider_models(http, config)
        require_exact_model(advertised, config.model)
        client = DeepSeekClient(
            http,
            config.base_url,
            config.api_key,
            config.model,
            config.timeout_seconds,
            config.max_retries,
        )
        for index, pair in enumerate(calls, 1):
            print(f"[{index}/{len(calls)}] {pair.scenario_id} repeat={pair.repeat} arm=raw_llm", flush=True)
            run_one(
                PROJECT_ROOT,
                runs_root,
                config,
                client,
                by_id[pair.scenario_id],
                pair.repeat,
                "raw_llm",
                force=args.force,
                execute_supported=not args.no_execute,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

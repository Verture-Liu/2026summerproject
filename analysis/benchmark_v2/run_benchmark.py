from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in [PROJECT_ROOT, PROJECT_ROOT / "src"]:
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from analysis.benchmark_v2.client import DeepSeekClient
from analysis.benchmark_v2.config import BenchmarkConfig, load_config
from analysis.benchmark_v2.io_utils import atomic_write_json, atomic_write_text, bundle_is_complete
from analysis.benchmark_v2.prompts import build_arm_system_prompt
from analysis.benchmark_v2.scenarios import Scenario, build_call_schedule, load_scenarios
from analysis.benchmark_v2.scoring import Score, score_completion
from research_agent.agent.models import Workflow
from research_agent.execution.executor import execute_workflow
from research_agent.skills.registry import build_default_registry


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "-c", "filter.lfs.process=", "-c", "filter.lfs.required=false", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _repair(client, system_prompt: str, instruction: str, invalid: str) -> object:
    return client.complete(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Original task: {instruction}\n"
                    "Repair the response below into exactly one JSON object matching either "
                    "WORKFLOW_JSON_SCHEMA or BLOCKED_JSON_SCHEMA. Preserve the intended task and return JSON only.\n"
                    f"INVALID_RESPONSE={invalid}"
                ),
            },
        ]
    )


def run_one(
    project_root: Path,
    runs_root: Path,
    config: BenchmarkConfig,
    client,
    scenario: Scenario,
    repeat: int,
    arm: str,
    *,
    force: bool = False,
    execute_supported: bool = True,
) -> Path:
    bundle = Path(runs_root) / scenario.id / f"repeat_{repeat:02d}" / arm
    if bundle_is_complete(bundle) and not force:
        return bundle
    bundle.mkdir(parents=True, exist_ok=True)
    system_prompt = build_arm_system_prompt(arm, scenario)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": scenario.instruction},
    ]
    atomic_write_json(
        bundle / "request.json",
        {
            "scenario_id": scenario.id,
            "repeat": repeat,
            "arm": arm,
            "messages": messages,
            "inputs": [
                {"ref": ref, "path": str(path.relative_to(project_root)), "sha256": _sha256(path)}
                for ref, path in zip(scenario.input_refs, scenario.input_paths)
            ],
            "api": config.redacted(),
        },
    )
    started = datetime.now(UTC)
    repairs = 0
    try:
        completion = client.complete(messages)
        atomic_write_text(bundle / "raw_completion.txt", completion.content)
        score = score_completion(completion.content, scenario)
        final_content = completion.content
        usage = dict(completion.usage)
        attempts = completion.attempts
        latency = completion.latency_seconds
        if score.decision == "parse_error":
            repaired = _repair(client, system_prompt, scenario.instruction, completion.content)
            repairs = 1
            atomic_write_text(bundle / "repair_completion.txt", repaired.content)
            final_content = repaired.content
            score = score_completion(final_content, scenario)
            attempts += repaired.attempts
            latency += repaired.latency_seconds
            for key, value in repaired.usage.items():
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
        if score.workflow is not None:
            atomic_write_json(bundle / "workflow.json", score.workflow)
        else:
            atomic_write_json(bundle / "decision.json", json.loads(final_content))

        score_payload = score.to_dict()
        if scenario.execute and execute_supported and score.strict_success and score.workflow is not None:
            workflow = Workflow.model_validate(score.workflow)
            execution = execute_workflow(
                workflow,
                bundle / "execution_task",
                dict(zip(scenario.input_refs, scenario.input_paths)),
                build_default_registry(),
                config.redacted(),
            )
            execution_payload = {
                "status": execution.status,
                "outputs": execution.outputs,
                "steps": execution.steps,
            }
            atomic_write_json(bundle / "execution.json", execution_payload)
            if execution.status != "succeeded":
                score_payload["strict_success"] = False
                score_payload["failure_codes"] = list(score.failure_codes) + ["execution_failed"]
        atomic_write_json(bundle / "score.json", score_payload)
        atomic_write_json(
            bundle / "provenance.json",
            {
                "scenario_id": scenario.id,
                "repeat": repeat,
                "arm": arm,
                "started_at": started.isoformat(),
                "ended_at": datetime.now(UTC).isoformat(),
                "model_reported": completion.model,
                "usage": usage,
                "latency_seconds": latency,
                "attempts": attempts,
                "repair_calls": repairs,
                "code_commit": _commit(project_root),
                "config": config.redacted(),
            },
        )
    except Exception as exc:
        atomic_write_json(bundle / "api_error.json", {"type": type(exc).__name__, "message": str(exc)})
        atomic_write_json(
            bundle / "score.json",
            Score(False, "api_error", ("api_error",)).to_dict(),
        )
        atomic_write_json(
            bundle / "provenance.json",
            {
                "scenario_id": scenario.id,
                "repeat": repeat,
                "arm": arm,
                "started_at": started.isoformat(),
                "ended_at": datetime.now(UTC).isoformat(),
                "code_commit": _commit(project_root),
                "config": config.redacted(),
            },
        )
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}:
            raise
    atomic_write_json(bundle / "complete.json", {"complete": True})
    return bundle


def local_check(project_root: Path, config: BenchmarkConfig, scenarios: list[Scenario]) -> dict:
    missing = [str(path) for scenario in scenarios for path in scenario.input_paths if not path.is_file()]
    output = project_root / "analysis" / "benchmark_v2" / "runs"
    output.mkdir(parents=True, exist_ok=True)
    return {
        "ok": not missing,
        "missing_inputs": missing,
        "scenario_count": len(scenarios),
        "formal_calls": len(scenarios) * 3 * 2,
        "config": config.redacted(),
        "runs_directory": str(output),
    }


def health_check(project_root: Path, config: BenchmarkConfig) -> dict:
    with httpx.Client(verify=True) as http:
        client = DeepSeekClient(http, config.base_url, config.api_key, config.model, config.timeout_seconds, config.max_retries)
        completion = client.complete(
            [
                {"role": "system", "content": "Return exactly one JSON object."},
                {"role": "user", "content": 'Return {"status":"ok"}.'},
            ]
        )
    record = {
        "excluded_from_formal_sample": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "model_reported": completion.model,
        "usage": completion.usage,
        "latency_seconds": completion.latency_seconds,
        "attempts": completion.attempts,
        "response_is_json": isinstance(json.loads(completion.content), dict),
        "config": config.redacted(),
    }
    atomic_write_json(project_root / "analysis" / "benchmark_v2" / "health_check.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-execute", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    config = load_config(PROJECT_ROOT / ".env")
    scenarios = load_scenarios(PROJECT_ROOT)
    if args.check:
        print(json.dumps(local_check(PROJECT_ROOT, config, scenarios), ensure_ascii=False, indent=2))
        return 0
    if args.health_check:
        print(json.dumps(health_check(PROJECT_ROOT, config), ensure_ascii=False, indent=2))
        return 0

    by_id = {scenario.id: scenario for scenario in scenarios}
    schedule = build_call_schedule(scenarios)
    calls = [(pair, arm) for pair in schedule for arm in pair.arm_order]
    if args.limit is not None:
        calls = calls[: args.limit]
    runs_root = PROJECT_ROOT / "analysis" / "benchmark_v2" / "runs"
    with httpx.Client(verify=True) as http:
        client = DeepSeekClient(http, config.base_url, config.api_key, config.model, config.timeout_seconds, config.max_retries)
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

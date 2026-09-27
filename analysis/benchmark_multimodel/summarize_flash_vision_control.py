from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for candidate in [ROOT, ROOT / "src"]:
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from analysis.benchmark_v2.io_utils import atomic_write_json
from analysis.benchmark_v2.scenarios import load_scenarios
from analysis.benchmark_v2.scoring import score_completion
from analysis.benchmark_v2.summary import exact_mcnemar, summarize_records, wilson


MANIFEST = ROOT / "analysis" / "benchmark_v5" / "heldout_manifest.json"
PRO_RUNS = ROOT / "analysis" / "benchmark_multimodel" / "v4_pro" / "runs"
BASELINE_FLASH_RUNS = ROOT / "analysis" / "benchmark_v5" / "runs"
CONTROL_ROOT = ROOT / "analysis" / "benchmark_multimodel" / "v4_flash_vision_exp"
CONTROL_RUNS = CONTROL_ROOT / "runs"
RESULTS = CONTROL_ROOT / "results"


def verified_records(runs_root: Path, arm: str, expected_model: str) -> tuple[list[dict], dict]:
    scenarios = {scenario.id: scenario for scenario in load_scenarios(ROOT, manifest_path=MANIFEST)}
    records = []
    discrepancies = []
    reported_models = set()
    api_errors = 0
    for score_path in sorted(runs_root.glob(f"*/repeat_*/{arm}/score.json")):
        bundle = score_path.parent
        scenario_id = bundle.parents[1].name
        repeat = int(bundle.parent.name.split("_")[-1])
        if (bundle / "api_error.json").exists():
            api_errors += 1
        provenance = json.loads((bundle / "provenance.json").read_text(encoding="utf-8"))
        if provenance.get("model_reported"):
            reported_models.add(provenance["model_reported"])
        completion_path = bundle / ("repair_completion.txt" if (bundle / "repair_completion.txt").exists() else "raw_completion.txt")
        stored = json.loads(score_path.read_text(encoding="utf-8"))
        if completion_path.exists():
            fresh = score_completion(completion_path.read_text(encoding="utf-8"), scenarios[scenario_id]).to_dict()
            execution_path = bundle / "execution.json"
            if execution_path.exists() and json.loads(execution_path.read_text(encoding="utf-8"))["status"] != "succeeded":
                fresh["strict_success"] = False
                fresh["failure_codes"] = list(fresh["failure_codes"]) + ["execution_failed"]
            for field in ["strict_success", "decision", "failure_codes"]:
                fresh_value = list(fresh[field]) if field == "failure_codes" else fresh[field]
                stored_value = list(stored[field]) if field == "failure_codes" else stored[field]
                if fresh_value != stored_value:
                    discrepancies.append({"bundle": str(bundle.relative_to(ROOT)), "field": field})
        records.append(
            {
                "scenario_id": scenario_id,
                "repeat": repeat,
                "arm": arm,
                "strict_success": bool(stored["strict_success"]),
                "decision": stored.get("decision"),
                "failure_codes": ";".join(stored.get("failure_codes", [])),
                "latency_seconds": provenance.get("latency_seconds"),
                "total_tokens": provenance.get("usage", {}).get("total_tokens"),
            }
        )
    verification = {
        "checked": len(records),
        "expected": 24,
        "all_match": len(records) == 24 and not discrepancies and reported_models == {expected_model},
        "discrepancies": discrepancies,
        "api_errors": api_errors,
        "reported_models": sorted(reported_models),
    }
    return records, verification


def operational_metrics(records: list[dict]) -> dict:
    latencies = [float(row["latency_seconds"]) for row in records if row.get("latency_seconds") is not None]
    tokens = [int(row["total_tokens"]) for row in records if row.get("total_tokens") is not None]
    return {
        "runs": len(records),
        "median_latency_seconds": statistics.median(latencies),
        "total_tokens": sum(tokens),
        "median_tokens": statistics.median(tokens),
    }


def paired_task_comparison(first: list[dict], second: list[dict], first_name: str, second_name: str) -> dict:
    first_map = {(row["scenario_id"], row["repeat"]): bool(row["strict_success"]) for row in first}
    second_map = {(row["scenario_id"], row["repeat"]): bool(row["strict_success"]) for row in second}
    if set(first_map) != set(second_map) or len(first_map) != 24:
        raise RuntimeError("Paired comparison does not contain the same 24 scenario/repeat units")
    first_successes = sum(first_map.values())
    second_successes = sum(second_map.values())
    first_only = sum(first_map[key] and not second_map[key] for key in first_map)
    second_only = sum(second_map[key] and not first_map[key] for key in first_map)
    first_ci = wilson(first_successes, 24)
    second_ci = wilson(second_successes, 24)
    return {
        first_name: {"successes": first_successes, "total": 24, "rate": first_successes / 24, "wilson_95": list(first_ci)},
        second_name: {"successes": second_successes, "total": 24, "rate": second_successes / 24, "wilson_95": list(second_ci)},
        "rate_difference_first_minus_second": first_successes / 24 - second_successes / 24,
        "discordant": {f"{first_name}_only": first_only, f"{second_name}_only": second_only},
        "mcnemar_exact_two_sided_p": exact_mcnemar(first_only, second_only),
    }


def main() -> None:
    pro_records, pro_verification = verified_records(PRO_RUNS, "paleorigor", "deepseek-v4-pro")
    baseline_flash_records, baseline_flash_verification = verified_records(
        BASELINE_FLASH_RUNS, "raw_llm", "deepseek-v4-flash"
    )
    control_records, control_verification = verified_records(
        CONTROL_RUNS, "raw_llm", "deepseek-v4-flash-vision-exp"
    )
    if not all(
        report["all_match"]
        for report in [pro_verification, baseline_flash_verification, control_verification]
    ):
        raise RuntimeError(
            "Independent verification failed: "
            f"pro={pro_verification}; baseline_flash={baseline_flash_verification}; "
            f"control={control_verification}"
        )

    records = pro_records + control_records
    summary = summarize_records(records)
    payload = {
        "comparison": "deepseek-v4-pro + PaleoRigor skills vs deepseek-v4-flash-vision-exp without skills",
        "design": "exploratory paired-task comparison; model and control layer both differ",
        "summary": summary,
        "new_model_vs_standard_flash_without_skills": paired_task_comparison(
            control_records,
            baseline_flash_records,
            "v4_flash_vision_exp_raw",
            "v4_flash_raw",
        ),
        "verification": {
            "v4_pro_paleorigor": pro_verification,
            "v4_flash_raw": baseline_flash_verification,
            "v4_flash_vision_exp_raw": control_verification,
        },
        "operational_metrics": {
            "v4_pro_paleorigor": operational_metrics(pro_records),
            "v4_flash_raw": operational_metrics(baseline_flash_records),
            "v4_flash_vision_exp_raw": operational_metrics(control_records),
        },
        "interpretation_boundary": (
            "The result describes performance on the frozen PaleoRigor task set. Because both the model "
            "and the presence of Skills differ, it does not isolate a causal Skills effect or establish "
            "general model superiority."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    atomic_write_json(RESULTS / "mixed_model_comparison.json", payload)
    with (RESULTS / "mixed_model_run_level.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "scenario_id", "repeat", "arm", "strict_success", "decision",
            "failure_codes", "latency_seconds", "total_tokens",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

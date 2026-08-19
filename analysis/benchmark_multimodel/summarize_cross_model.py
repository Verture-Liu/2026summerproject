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

from analysis.benchmark_v2.scenarios import load_scenarios
from analysis.benchmark_v2.scoring import score_completion


FLASH_SUMMARY = ROOT / "analysis/benchmark_v5/results/summary.json"
PRO_ROOT = ROOT / "analysis/benchmark_multimodel/v4_pro"
PRO_RUNS = PRO_ROOT / "runs"
PRO_SUMMARY = PRO_ROOT / "results/summary.json"
MANIFEST = ROOT / "analysis/benchmark_v5/heldout_manifest.json"


def independently_verify() -> dict:
    scenarios = {s.id: s for s in load_scenarios(ROOT, manifest_path=MANIFEST)}
    discrepancies = []
    checked = 0
    reported_models = set()
    api_errors = 0
    for score_path in sorted(PRO_RUNS.glob("*/repeat_*/*/score.json")):
        bundle = score_path.parent
        if (bundle / "api_error.json").exists():
            api_errors += 1
        provenance = json.loads((bundle / "provenance.json").read_text(encoding="utf-8"))
        if provenance.get("model_reported"):
            reported_models.add(provenance["model_reported"])
        content_path = bundle / ("repair_completion.txt" if (bundle / "repair_completion.txt").exists() else "raw_completion.txt")
        if not content_path.exists():
            continue
        fresh = score_completion(content_path.read_text(encoding="utf-8"), scenarios[bundle.parents[1].name]).to_dict()
        execution_path = bundle / "execution.json"
        if execution_path.exists() and json.loads(execution_path.read_text(encoding="utf-8"))["status"] != "succeeded":
            fresh["strict_success"] = False
            fresh["failure_codes"] = list(fresh["failure_codes"]) + ["execution_failed"]
        stored = json.loads(score_path.read_text(encoding="utf-8"))
        checked += 1
        for field in ["strict_success", "decision", "failure_codes"]:
            fresh_value = list(fresh[field]) if field == "failure_codes" else fresh[field]
            stored_value = list(stored[field]) if field == "failure_codes" else stored[field]
            if fresh_value != stored_value:
                discrepancies.append({"bundle": str(bundle.relative_to(ROOT)), "field": field})
    return {
        "checked": checked,
        "expected": 48,
        "all_match": checked == 48 and not discrepancies,
        "discrepancies": discrepancies,
        "api_errors": api_errors,
        "reported_models": sorted(reported_models),
    }


def operational_metrics() -> dict:
    rows = list(csv.DictReader((PRO_ROOT / "results/run_level.csv").open(encoding="utf-8")))
    output = {}
    for arm in ["paleorigor", "raw_llm"]:
        selected = [r for r in rows if r["arm"] == arm]
        latencies = [float(r["latency_seconds"]) for r in selected if r["latency_seconds"]]
        tokens = [int(r["total_tokens"]) for r in selected if r["total_tokens"]]
        output[arm] = {
            "runs": len(selected),
            "median_latency_seconds": statistics.median(latencies),
            "total_tokens": sum(tokens),
            "median_tokens": statistics.median(tokens),
        }
    return output


def main() -> None:
    flash = json.loads(FLASH_SUMMARY.read_text(encoding="utf-8"))
    pro = json.loads(PRO_SUMMARY.read_text(encoding="utf-8"))
    verification = independently_verify()
    if not verification["all_match"]:
        raise RuntimeError(f"Independent verification failed: {verification}")

    decision = (
        pro["arms"]["paleorigor"]["successes"] >= 22
        and pro["arms"]["paleorigor"]["successes"] > pro["arms"]["raw_llm"]["successes"]
    )
    payload = {
        "preregistered_h1_supported": decision,
        "flash_context_already_observed": flash,
        "pro_confirmatory_sample": pro,
        "verification": verification,
        "operational_metrics": operational_metrics(),
        "interpretation": (
            "The preregistered engineering criterion was met on V4-Pro. "
            "Inference remains limited by 24 pairs and one API provider; this is not a vendor ranking."
        ),
    }
    results = PRO_ROOT / "results"
    (results / "cross_model_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (results / "model_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["model", "arm", "successes", "total", "rate", "wilson_low", "wilson_high", "paired_difference", "mcnemar_p"],
        )
        writer.writeheader()
        for model, summary in [("deepseek-v4-flash", flash), ("deepseek-v4-pro", pro)]:
            for arm in ["paleorigor", "raw_llm"]:
                values = summary["arms"][arm]
                writer.writerow({
                    "model": model,
                    "arm": arm,
                    "successes": values["successes"],
                    "total": values["total"],
                    "rate": values["rate"],
                    "wilson_low": values["wilson_95"][0],
                    "wilson_high": values["wilson_95"][1],
                    "paired_difference": summary["paired_rate_difference"],
                    "mcnemar_p": summary["mcnemar_exact_two_sided_p"],
                })

    report = f"""# Cross-model robustness verification\n\n- Frozen code commit before the first Pro call: `728a226`\n- Formal Pro calls: {verification['checked']}/48\n- API errors: {verification['api_errors']}\n- Independently rescored labels: {verification['checked']}/48 matched\n- Provider-reported model: {', '.join(verification['reported_models'])}\n- Pro/PaleoRigor: {pro['arms']['paleorigor']['successes']}/24 ({pro['arms']['paleorigor']['rate']:.1%})\n- Pro/raw model: {pro['arms']['raw_llm']['successes']}/24 ({pro['arms']['raw_llm']['rate']:.1%})\n- Paired difference: {pro['paired_rate_difference']:.1%}\n- Discordant pairs: PaleoRigor-only {pro['discordant']['paleorigor_only']}; raw-only {pro['discordant']['raw_only']}\n- Exact two-sided McNemar p: {pro['mcnemar_exact_two_sided_p']:.4f}\n- Preregistered criterion met: {'yes' if decision else 'no'}\n\nThis is a same-provider robustness check. It does not rank model vendors or establish universal LLM generalization.\n"""
    (results / "verification_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

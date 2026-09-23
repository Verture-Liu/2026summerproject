"""Build the public benchmark-explorer payload from the retained v5 run records.

Reads only files already committed to the public repository. Carries no
credentials: the request records store `api_key_present` as a boolean and the
key itself is never written to disk.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "analysis/benchmark_v5/runs"
MANIFEST = ROOT / "analysis/benchmark_v5/heldout_manifest.json"
SUMMARY = ROOT / "analysis/benchmark_v5/results/summary.json"
PRO_SUMMARY = ROOT / "analysis/benchmark_multimodel/v4_pro/results/summary.json"
OUT = ROOT / "docs/data/benchmark_v5.json"

ARMS = ("paleorigor", "raw_llm")


def compact_steps(workflow):
    if not workflow:
        return []
    out = []
    for s in workflow.get("steps", []):
        out.append({
            "id": s.get("id"),
            "skill": s.get("skill"),
            "inputs": [i.get("ref") or i.get("source") for i in s.get("inputs", [])],
            "outputs": [o.get("name") for o in s.get("outputs", [])],
            "reason": (s.get("reason") or "")[:240],
        })
    return out


def read_run(scenario_id: str, repeat: int, arm: str):
    d = RUNS / scenario_id / f"repeat_{repeat:02d}" / arm
    if not d.is_dir():
        return None
    score = json.loads((d / "score.json").read_text())
    prov = json.loads((d / "provenance.json").read_text())
    rec = {
        "repeat": repeat,
        "success": bool(score["strict_success"]),
        "decision": score["decision"],
        "failure_codes": score.get("failure_codes", []),
        "steps": compact_steps(score.get("workflow")),
        "latency_s": round(prov.get("latency_seconds", 0), 1),
        "attempts": prov.get("attempts"),
        "repair_calls": prov.get("repair_calls", 0),
        "tokens": (prov.get("usage") or {}).get("total_tokens"),
    }
    if score["decision"] == "blocked":
        raw = (d / "raw_completion.txt").read_text(encoding="utf-8").strip()
        try:
            blocked = json.loads(raw)
            rec["reason_code"] = blocked.get("reason_code")
            rec["message"] = blocked.get("message", "")
        except json.JSONDecodeError:
            rec["message"] = raw[:400]
    return rec


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    summary = json.loads(SUMMARY.read_text())
    pro = json.loads(PRO_SUMMARY.read_text())

    scenarios = []
    for sc in manifest["scenarios"]:
        entry = {
            "id": sc["id"],
            "class": sc["class"],
            "instruction": sc["instruction"],
            "inputs": [Path(p).name for p in sc.get("inputs", [])],
            "required_skills": sc.get("required_skills", []),
            "forbidden_skills": sc.get("forbidden_skills", []),
            "expected_reason_code": sc.get("expected_reason_code"),
            "executed": sc.get("execute", False),
            "runs": {},
        }
        for arm in ARMS:
            runs = [r for r in (read_run(sc["id"], i, arm) for i in (1, 2, 3)) if r]
            entry["runs"][arm] = runs
        scenarios.append(entry)

    payload = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "release": "v0.2.0",
        "doi": "10.5281/zenodo.22912729",
        "repeats": manifest["repeats"],
        "models": {"primary": "deepseek-v4-flash", "second": "deepseek-v4-pro"},
        "summary": {
            "flash": {a: {"successes": summary["arms"][a]["successes"], "total": summary["arms"][a]["total"],
                          "wilson": [round(x * 100, 1) for x in summary["arms"][a]["wilson_95"]]} for a in ARMS},
            "pro": {a: {"successes": pro["arms"][a]["successes"], "total": pro["arms"][a]["total"],
                        "wilson": [round(x * 100, 1) for x in pro["arms"][a]["wilson_95"]]} for a in ARMS},
            "mcnemar_flash_p": summary["mcnemar_exact_two_sided_p"],
            "mcnemar_pro_p": pro["mcnemar_exact_two_sided_p"],
        },
        "scenarios": scenarios,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # sanity: the payload must reproduce the published headline numbers
    flat = [r for s in scenarios for a in ARMS for r in s["runs"][a]]
    pr = [r for s in scenarios for r in s["runs"]["paleorigor"]]
    rw = [r for s in scenarios for r in s["runs"]["raw_llm"]]
    assert len(flat) == 48, f"expected 48 runs, got {len(flat)}"
    assert sum(r["success"] for r in pr) == summary["arms"]["paleorigor"]["successes"] == 23
    assert sum(r["success"] for r in rw) == summary["arms"]["raw_llm"]["successes"] == 19
    blocked_ok = [r for s in scenarios if s["class"] == "boundary" for r in s["runs"]["paleorigor"]
                  if r["decision"] == "blocked" and r.get("reason_code") == s["expected_reason_code"]]
    assert len(blocked_ok) == 12, f"expected 12 correct refusals, got {len(blocked_ok)}"

    print(f"  OK  48 runs extracted; PaleoRigor 23/24, ablated 19/24 — matches summary.json")
    print(f"  OK  12/12 boundary refusals carry the prespecified reason code")
    print(f"  OK  no credential fields present: "
          f"{not any('api_key' in json.dumps(s) for s in scenarios)}")
    print(f"\nWrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()

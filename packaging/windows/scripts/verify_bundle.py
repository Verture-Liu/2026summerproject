#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


VERSION_ARGS = {
    "fastqc": ["--version"],
    "multiqc": ["--version"],
    "seqkit": ["version"],
    "seqtk": [],
    "samtools": ["--version"],
    "bwa": [],
    "bowtie2": ["--version"],
}


def verify(tool_root: Path) -> dict:
    manifest = json.loads((tool_root / "manifest.json").read_text(encoding="utf-8"))
    results = []
    for item in manifest["tools"]:
        command = tool_root / item["command"]
        if not command.is_file():
            raise FileNotFoundError(f"missing bundled command: {command}")
        completed = subprocess.run(
            [str(command), *VERSION_ARGS[item["id"]]],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        output = (completed.stdout + completed.stderr).strip()
        results.append({"id": item["id"], "returncode": completed.returncode, "output": output[:1000]})
    return {"passed": all(item["returncode"] in {0, 1} for item in results), "tools": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tool_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.tool_root.resolve())
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

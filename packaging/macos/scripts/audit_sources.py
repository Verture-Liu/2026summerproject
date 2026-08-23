from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def architecture(path: Path) -> str:
    result = subprocess.run(
        ["/usr/bin/file", "-b", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return "arm64" if "arm64" in result else "script" if "script" in result.lower() else "unknown"


def audit(config_path: Path) -> dict[str, object]:
    sources = json.loads(config_path.read_text(encoding="utf-8"))
    audited: dict[str, object] = {}
    for name, values in sources.items():
        source = Path(values["source"])
        if not source.exists():
            raise FileNotFoundError(f"Missing packaging source for {name}: {source}")
        record = {"version": values["version"], "source": str(source), "upstream": values["upstream"]}
        if source.is_file():
            record.update({"sha256": sha256(source), "architecture": architecture(source)})
        else:
            record.update({"sha256": None, "architecture": "directory"})
        audited[name] = record
    return {"schema_version": 1, "tools": audited}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path(__file__).parents[1] / "tool-sources.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

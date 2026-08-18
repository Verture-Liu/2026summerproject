from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    id: str
    kind: str
    input_paths: tuple[Path, ...]
    instruction: str
    required_skills: tuple[str, ...]
    forbidden_skills: tuple[str, ...]
    expected_reason_code: str | None
    execute: bool

    @property
    def input_refs(self) -> tuple[str, ...]:
        return tuple(path.name for path in self.input_paths)

    @property
    def uploaded_formats(self) -> dict[str, str]:
        return {ref: _format_for(path) for ref, path in zip(self.input_refs, self.input_paths)}

    @property
    def file_summaries(self) -> list[dict[str, object]]:
        return [
            {
                "ref": ref,
                "name": path.name,
                "format": _format_for(path),
                "size_bytes": path.stat().st_size,
            }
            for ref, path in zip(self.input_refs, self.input_paths)
        ]


@dataclass(frozen=True)
class CallPair:
    scenario_id: str
    repeat: int
    arm_order: tuple[str, str]


def _format_for(path: Path) -> str:
    name = path.name.lower()
    if name.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
        return "fastq"
    if name.endswith(".csv"):
        return "csv"
    if name.endswith(".tsv"):
        return "tsv"
    return "unknown"


def load_scenarios(root: Path) -> list[Scenario]:
    root = Path(root).resolve()
    manifest_path = Path(__file__).with_name("scenario_manifest.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenarios = []
    for item in payload["scenarios"]:
        paths = tuple((root / relative).resolve() for relative in item["inputs"])
        if not all(path.is_relative_to(root) for path in paths):
            raise ValueError(f"Scenario {item['id']} escapes the project root")
        if item["class"] == "boundary" and item["execute"]:
            raise ValueError(f"Boundary scenario {item['id']} cannot execute")
        scenarios.append(
            Scenario(
                id=item["id"],
                kind=item["class"],
                input_paths=paths,
                instruction=item["instruction"],
                required_skills=tuple(item["required_skills"]),
                forbidden_skills=tuple(item["forbidden_skills"]),
                expected_reason_code=item["expected_reason_code"],
                execute=bool(item["execute"]),
            )
        )
    return scenarios


def build_call_schedule(scenarios: list[Scenario], repeats: int = 3) -> list[CallPair]:
    pairs = []
    index = 0
    for scenario in scenarios:
        for repeat in range(1, repeats + 1):
            first = "raw_llm" if index % 2 == 0 else "paleorigor"
            second = "paleorigor" if first == "raw_llm" else "raw_llm"
            pairs.append(CallPair(scenario.id, repeat, (first, second)))
            index += 1
    return pairs

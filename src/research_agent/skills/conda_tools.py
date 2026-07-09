from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ToolCommand:
    tool: str
    command: list[str]
    source: str


def _config_path() -> Path:
    return Path.cwd() / "config" / "tool_envs.json"


@lru_cache(maxsize=1)
def load_tool_envs() -> dict[str, str]:
    path = _config_path()
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def resolve_tool(
    executable_candidates: Sequence[str],
    tool_envs: Mapping[str, str] | None = None,
) -> ToolCommand | None:
    mapping = load_tool_envs() if tool_envs is None else dict(tool_envs)
    for name in executable_candidates:
        executable = shutil.which(name)
        if executable:
            return ToolCommand(tool=name, command=[executable], source="path")
    conda = shutil.which("conda")
    if not conda:
        default_conda = Path("/opt/miniconda3/bin/conda")
        conda = str(default_conda) if default_conda.exists() else None
    if conda:
        for name in executable_candidates:
            env = mapping.get(name)
            if env:
                return ToolCommand(
                    tool=name,
                    command=[conda, "run", "-n", env, name],
                    source=f"conda:{env}",
                )
    return None


def run_tool_command(
    tool_command: ToolCommand,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*tool_command.command, *[str(arg) for arg in args]],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

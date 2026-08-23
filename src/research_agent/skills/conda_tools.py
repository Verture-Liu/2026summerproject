from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Sequence

from research_agent.runtime.paths import is_packaged_runtime, resource_root


@dataclass(frozen=True)
class ToolCommand:
    tool: str
    command: list[str]
    source: str


def _config_path() -> Path:
    return Path.cwd() / "config" / "tool_envs.json"


def bundled_tool_root(env: Mapping[str, str] | None = None) -> Path | None:
    source = os.environ if env is None else env
    configured_root = source.get("PALEORIGOR_TOOL_ROOT")
    if configured_root:
        root = Path(configured_root).expanduser()
        return root if root.is_dir() else None
    packaged_root = resource_root() / "tools"
    return packaged_root if packaged_root.is_dir() else None


def _bundled_tool_command(
    executable_candidates: Sequence[str], bundle_root: Path
) -> ToolCommand | None:
    manifest_path = resource_root() / "resources" / "tool_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    tools = manifest.get("tools") if isinstance(manifest, dict) else None
    if not isinstance(tools, list):
        return None

    resolved_root = bundle_root.resolve()
    for name in executable_candidates:
        for entry in tools:
            if not isinstance(entry, dict) or entry.get("id") != name:
                continue
            command = entry.get("command")
            if not isinstance(command, str):
                continue
            candidate = (bundle_root / command).resolve()
            if resolved_root not in candidate.parents:
                continue
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return ToolCommand(tool=name, command=[str(candidate)], source="bundle")
    return None


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
    bundle_root: Path | str | None = None,
    packaged: bool | None = None,
) -> ToolCommand | None:
    root = Path(bundle_root).expanduser() if bundle_root is not None else bundled_tool_root()
    if root is not None:
        bundled = _bundled_tool_command(executable_candidates, root)
        if bundled is not None:
            return bundled
    if is_packaged_runtime(packaged):
        return None

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
                env_path = Path(env).expanduser()
                if not env_path.is_absolute():
                    conda_root = Path(conda).resolve().parent.parent
                    env_path = conda_root / "envs" / env
                executable_path = env_path / "bin" / name
                if not executable_path.is_file():
                    continue
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

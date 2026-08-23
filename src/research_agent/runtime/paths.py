from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


def resource_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    return Path(frozen_root) / "research_agent" if frozen_root else Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppPaths:
    support_dir: Path
    preferences_file: Path
    task_root: Path
    cache_dir: Path
    log_dir: Path
    installed_skill_root: Path

    @classmethod
    def for_runtime(cls, home: Path | None = None, env: Mapping[str, str] | None = None) -> "AppPaths":
        source = os.environ if env is None else env
        home = Path.home() if home is None else Path(home)
        override = source.get("PALEORIGOR_DATA_ROOT")
        if override:
            root = Path(override).expanduser().resolve()
            support, cache, logs = root / "support", root / "cache", root / "logs"
        else:
            support = home / "Library/Application Support/PaleoRigor"
            cache = home / "Library/Caches/PaleoRigor"
            logs = home / "Library/Logs/PaleoRigor"
        return cls(support, support / "preferences.json", cache / "tasks", cache, logs, support / "skills")

    def ensure(self) -> None:
        for path in [self.support_dir, self.task_root, self.cache_dir, self.log_dir, self.installed_skill_root]:
            path.mkdir(parents=True, exist_ok=True)

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Mapping


_PREFERENCE_KEYS = ("api_base_url", "model", "language")


class JsonPreferences:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> dict[str, str]:
        if not self.path.is_file():
            return {}
        values = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: values[key] for key in _PREFERENCE_KEYS if key in values}

    def save(self, values: Mapping[str, str]) -> None:
        selected = {key: values[key] for key in _PREFERENCE_KEYS if key in values}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(selected, temporary, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

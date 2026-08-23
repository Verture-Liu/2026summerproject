from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class SecretContaminationError(RuntimeError):
    """Raised without echoing the secret when data contains a configured secret."""

    def __init__(self) -> None:
        super().__init__("Secret-contaminated data was rejected")


def assert_no_secret_contamination(value: Any, secret: str) -> None:
    """Reject any exact nonempty secret occurring in nested string keys or values."""
    if not secret:
        return

    def scan(candidate: Any) -> None:
        if isinstance(candidate, str):
            if secret in candidate:
                raise SecretContaminationError()
            return
        if isinstance(candidate, Mapping):
            for key, nested_value in candidate.items():
                scan(key)
                scan(nested_value)
            return
        if isinstance(candidate, (list, tuple, set, frozenset)):
            for nested_value in candidate:
                scan(nested_value)

    scan(value)


def write_guarded_json(path: Path, value: Any, secret: str, *, indent: int = 2) -> None:
    """Check before serialization, then write JSON only when the payload is clean."""
    assert_no_secret_contamination(value, secret)
    serialized = json.dumps(value, ensure_ascii=False, indent=indent)
    path.write_text(serialized, encoding="utf-8")

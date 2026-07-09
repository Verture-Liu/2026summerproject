import json
from pathlib import Path


STATE_FILE = "output_destination.json"


def save_output_directory(task_dir: Path, selected: Path) -> None:
    task_dir = Path(task_dir)
    selected = Path(selected).expanduser().resolve()
    if not selected.exists() or not selected.is_dir():
        raise ValueError("Selected output path must be an existing directory")
    (task_dir / STATE_FILE).write_text(
        json.dumps({"path": str(selected)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_output_directory(task_dir: Path) -> Path | None:
    state = Path(task_dir) / STATE_FILE
    if not state.exists():
        return None
    selected = Path(json.loads(state.read_text(encoding="utf-8"))["path"])
    if not selected.exists() or not selected.is_dir():
        return None
    return selected.resolve()

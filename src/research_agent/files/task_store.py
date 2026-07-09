import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class StoredFile:
    ref: str
    path: Path
    sha256: str


class TaskStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def create_task(self) -> str:
        task_id = uuid.uuid4().hex
        for name in ("inputs", "steps", "outputs", "figures", "logs"):
            (self.root / task_id / name).mkdir(parents=True, exist_ok=True)
        return task_id

    def task_dir(self, task_id: str) -> Path:
        if not task_id.isalnum():
            raise ValueError("Invalid task id")
        path = self.root / task_id
        if not path.exists():
            raise FileNotFoundError(task_id)
        return path

    def add_input(self, task_id: str, filename: str, stream: BinaryIO) -> StoredFile:
        safe_name = Path(filename).name
        if not safe_name:
            raise ValueError("Filename is required")
        destination = self.task_dir(task_id) / "inputs" / safe_name
        with destination.open("wb") as handle:
            shutil.copyfileobj(stream, handle)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return StoredFile(destination.stem, destination, digest)

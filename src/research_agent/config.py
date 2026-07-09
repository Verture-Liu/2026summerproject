from dataclasses import asdict, dataclass
from os import environ
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    timeout_seconds: float = 60.0
    max_retries: int = 2
    task_root: str = "workspace/tasks"

    @classmethod
    def load(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = environ if env is None else env
        return cls(
            api_base_url=source.get("AGENT_API_BASE_URL", "https://api.openai.com/v1"),
            api_key=source.get("AGENT_API_KEY", ""),
            model=source.get("AGENT_MODEL", ""),
            timeout_seconds=float(source.get("AGENT_TIMEOUT_SECONDS", "60")),
            max_retries=int(source.get("AGENT_MAX_RETRIES", "2")),
            task_root=source.get("AGENT_TASK_ROOT", "workspace/tasks"),
        )

    def redacted(self) -> dict[str, object]:
        data = asdict(self)
        data["api_key"] = "***" if self.api_key else ""
        return data

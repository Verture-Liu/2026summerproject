from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class BenchmarkConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
    max_retries: int

    def redacted(self) -> dict:
        payload = asdict(self)
        payload.pop("api_key")
        payload["api_key_present"] = bool(self.api_key)
        payload["thinking"] = "enabled"
        payload["temperature"] = 0
        return payload


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config(path: Path) -> BenchmarkConfig:
    values = _parse_env(path)
    missing = [key for key in ["AGENT_API_BASE_URL", "AGENT_API_KEY", "AGENT_MODEL"] if not values.get(key)]
    if missing:
        raise ValueError(f"Missing environment setting(s): {', '.join(missing)}")
    model = values["AGENT_MODEL"]
    if model != "deepseek-v4-flash":
        raise ValueError(f"Frozen benchmark model must be deepseek-v4-flash, observed {model}")
    return BenchmarkConfig(
        base_url=values["AGENT_API_BASE_URL"].rstrip("/"),
        api_key=values["AGENT_API_KEY"],
        model=model,
        timeout_seconds=float(values.get("AGENT_TIMEOUT_SECONDS", "120")),
        max_retries=int(values.get("AGENT_MAX_RETRIES", "2")),
    )


def load_config_for_model(path: Path, model: str) -> BenchmarkConfig:
    """Load the existing API credentials with a prespecified benchmark model.

    The original ``load_config`` remains locked to V4-Flash so historical v5
    commands cannot silently change model. Cross-model experiments must call
    this explicit function and may select only the preregistered V4 models.
    """
    allowed = {"deepseek-v4-flash", "deepseek-v4-pro"}
    if model not in allowed:
        raise ValueError(
            "Allowed cross-model benchmark models are " + ", ".join(sorted(allowed))
        )
    values = _parse_env(path)
    missing = [key for key in ["AGENT_API_BASE_URL", "AGENT_API_KEY"] if not values.get(key)]
    if missing:
        raise ValueError(f"Missing environment setting(s): {', '.join(missing)}")
    return BenchmarkConfig(
        base_url=values["AGENT_API_BASE_URL"].rstrip("/"),
        api_key=values["AGENT_API_KEY"],
        model=model,
        timeout_seconds=float(values.get("AGENT_TIMEOUT_SECONDS", "120")),
        max_retries=int(values.get("AGENT_MAX_RETRIES", "2")),
    )

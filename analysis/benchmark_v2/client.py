from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class Completion:
    content: str
    model: str
    usage: dict[str, Any]
    latency_seconds: float
    attempts: int


class DeepSeekClient:
    def __init__(self, http: httpx.Client, base_url: str, api_key: str, model: str, timeout: float, max_retries: int):
        self.http = http
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def complete(self, messages: list[dict[str, str]]) -> Completion:
        started = time.monotonic()
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = self.http.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "temperature": 0,
                        "thinking": {"type": "enabled"},
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=self.timeout,
                )
                if response.status_code in {401, 403}:
                    response.raise_for_status()
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                payload = response.json()
                return Completion(
                    content=payload["choices"][0]["message"]["content"],
                    model=payload.get("model", self.model),
                    usage=payload.get("usage", {}),
                    latency_seconds=time.monotonic() - started,
                    attempts=attempt,
                )
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}:
                    raise
                if attempt > self.max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 4))
        raise RuntimeError("Completion failed") from last_error

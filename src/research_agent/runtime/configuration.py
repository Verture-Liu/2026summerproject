from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from research_agent.runtime.preferences import JsonPreferences
from research_agent.runtime.secrets import SecretStore


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
_API_KEY_ACCOUNT = "api_key"


@dataclass(frozen=True)
class RuntimeApiConfig:
    base_url: str
    model: str
    api_key: str


class RuntimeConfiguration:
    def __init__(self, preferences: JsonPreferences, secret_store: SecretStore):
        self._preferences = preferences
        self._secret_store = secret_store

    def get(self) -> RuntimeApiConfig:
        preferences = self._preferences.load()
        return RuntimeApiConfig(
            base_url=preferences.get("api_base_url", DEFAULT_BASE_URL),
            model=preferences.get("model", DEFAULT_MODEL),
            api_key=self._secret_store.get(_API_KEY_ACCOUNT) or "",
        )

    def update(self, base_url: str, model: str, api_key: str | None) -> dict[str, object]:
        normalized_base_url = self._normalize_base_url(base_url)
        normalized_model = model.strip()
        if not normalized_model:
            raise ValueError("Model must not be empty")

        old_preferences = self._preferences.load()
        updated_preferences = dict(old_preferences)
        updated_preferences["api_base_url"] = normalized_base_url
        updated_preferences["model"] = normalized_model

        normalized_api_key = api_key.strip() if api_key is not None else ""
        key_will_change = bool(normalized_api_key)
        old_api_key = self._secret_store.get(_API_KEY_ACCOUNT) if key_will_change else None

        if key_will_change:
            self._secret_store.set(_API_KEY_ACCOUNT, normalized_api_key)

        try:
            self._preferences.save(updated_preferences)
        except Exception as preference_error:
            rollback_errors = []
            if key_will_change:
                try:
                    if old_api_key:
                        self._secret_store.set(_API_KEY_ACCOUNT, old_api_key)
                    else:
                        self._secret_store.delete(_API_KEY_ACCOUNT)
                except Exception as exc:
                    rollback_errors.append(exc)
            try:
                self._preferences.save(old_preferences)
            except Exception as exc:
                rollback_errors.append(exc)
            if rollback_errors:
                raise RuntimeError("Configuration rollback failed") from preference_error
            raise

        return self._redacted(self.get())

    def delete_api_key(self) -> None:
        self._secret_store.delete(_API_KEY_ACCOUNT)

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized_base_url = base_url.strip()
        parsed = urlsplit(normalized_base_url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Base URL must use HTTP(S)")
        return normalized_base_url

    @staticmethod
    def _redacted(config: RuntimeApiConfig) -> dict[str, object]:
        return {
            "base_url": config.base_url,
            "model": config.model,
            "api_key_present": bool(config.api_key),
        }

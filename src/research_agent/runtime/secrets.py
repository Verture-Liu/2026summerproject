from __future__ import annotations

import subprocess
from typing import Callable, Protocol, Sequence


class SecretStore(Protocol):
    def get(self, name: str) -> str | None: ...

    def set(self, name: str, value: str) -> None: ...

    def delete(self, name: str) -> None: ...


class SecretStoreError(RuntimeError):
    pass


class MemorySecretStore:
    def __init__(self):
        self._values: dict[str, str] = {}

    def get(self, name: str) -> str | None:
        return self._values.get(name)

    def set(self, name: str, value: str) -> None:
        self._values[name] = value

    def delete(self, name: str) -> None:
        self._values.pop(name, None)


Runner = Callable[..., subprocess.CompletedProcess[str]]


class MacOSKeychainSecretStore:
    def __init__(self, service: str = "org.paleorigor.app", runner: Runner = subprocess.run):
        self.service = service
        self._runner = runner

    def __repr__(self) -> str:
        return f"MacOSKeychainSecretStore(service={self.service!r})"

    def get(self, name: str) -> str | None:
        result = self._run(
            ["/usr/bin/security", "find-generic-password", "-s", self.service, "-a", name, "-w"]
        )
        if result.returncode == 44:
            return None
        self._check_result(result)
        return result.stdout.rstrip("\r\n")

    def set(self, name: str, value: str) -> None:
        result = self._run(
            [
                "/usr/bin/security",
                "add-generic-password",
                "-U",
                "-s",
                self.service,
                "-a",
                name,
                "-w",
                value,
            ]
        )
        self._check_result(result)

    def delete(self, name: str) -> None:
        result = self._run(
            [
                "/usr/bin/security",
                "delete-generic-password",
                "-s",
                self.service,
                "-a",
                name,
            ]
        )
        if result.returncode == 44:
            return
        self._check_result(result)

    def _run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return self._runner(args, capture_output=True, text=True, check=False, shell=False)

    @staticmethod
    def _check_result(result: subprocess.CompletedProcess[str]) -> None:
        if result.returncode != 0:
            raise SecretStoreError("macOS Keychain operation failed")

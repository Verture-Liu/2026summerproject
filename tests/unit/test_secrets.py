import subprocess

import pytest

from research_agent.runtime.secrets import (
    MacOSKeychainSecretStore,
    MemorySecretStore,
    SecretStoreError,
)


SECRET = "fixture-secret"


class FakeRunner:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return next(self.responses)


def test_memory_secret_store_round_trip():
    store = MemorySecretStore()

    assert store.get("api_key") is None
    store.set("api_key", SECRET)
    assert store.get("api_key") == SECRET
    store.delete("api_key")
    assert store.get("api_key") is None


def test_keychain_store_uses_exact_security_commands_without_real_keychain():
    runner = FakeRunner(
        [
            subprocess.CompletedProcess([], 0, stdout=SECRET + "\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ]
    )
    store = MacOSKeychainSecretStore(runner=runner)

    assert store.get("api_key") == SECRET
    store.set("api_key", SECRET)
    store.delete("api_key")

    assert [call[0] for call in runner.calls] == [
        ["/usr/bin/security", "find-generic-password", "-s", "org.paleorigor.app", "-a", "api_key", "-w"],
        ["/usr/bin/security", "add-generic-password", "-U", "-s", "org.paleorigor.app", "-a", "api_key", "-w", SECRET],
        ["/usr/bin/security", "delete-generic-password", "-s", "org.paleorigor.app", "-a", "api_key"],
    ]


def test_keychain_not_found_is_none():
    runner = FakeRunner([subprocess.CompletedProcess([], 44, stdout="", stderr="not found")])

    assert MacOSKeychainSecretStore(runner=runner).get("api_key") is None


def test_keychain_errors_and_repr_redact_secret():
    runner = FakeRunner([subprocess.CompletedProcess([], 1, stdout="", stderr=SECRET)])
    store = MacOSKeychainSecretStore(runner=runner)

    with pytest.raises(SecretStoreError) as error:
        store.get("api_key")

    assert SECRET not in str(error.value)
    assert SECRET not in repr(store)

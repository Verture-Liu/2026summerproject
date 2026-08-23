import pytest

from research_agent.runtime.secret_guard import (
    SecretContaminationError,
    assert_no_secret_contamination,
)


def test_secret_guard_recursively_rejects_secret_in_strings_keys_and_values():
    secret = "configured-provider-secret"
    contaminated_payloads = [
        {"outer": ["safe", {"nested": f"prefix-{secret}-suffix"}]},
        {secret: "safe"},
        {"outer": {"nested": secret}},
    ]

    for payload in contaminated_payloads:
        with pytest.raises(SecretContaminationError) as caught:
            assert_no_secret_contamination(payload, secret)
        assert secret not in str(caught.value)


def test_secret_guard_does_not_false_match_an_empty_secret():
    assert_no_secret_contamination(
        {"empty": "", "nested": ["ordinary workflow text"]},
        "",
    )

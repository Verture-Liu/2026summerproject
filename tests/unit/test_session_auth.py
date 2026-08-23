import logging

from fastapi.testclient import TestClient

from research_agent.main import create_app


def test_session_token_guard_protects_api_without_leaking_tokens(tmp_path, caplog):
    expected_token = "fixed-token"
    supplied_token = "wrong-token"
    client = TestClient(create_app(task_root=tmp_path, session_token=expected_token))

    with caplog.at_level(logging.DEBUG):
        root = client.get("/")
        static_asset = client.get("/assets/styles.css")
        missing = client.get("/api/health")
        wrong = client.get("/api/health", headers={"X-PaleoRigor-Token": supplied_token})
        authorized = client.get("/api/health", headers={"X-PaleoRigor-Token": expected_token})

    assert root.status_code == 200
    assert static_asset.status_code == 200
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json() == {"status": "ok", "version": "0.2.0"}
    assert missing.json() == {"detail": {"error": "invalid_session"}}
    assert wrong.json() == {"detail": {"error": "invalid_session"}}

    emitted_text = "\n".join(record.getMessage() for record in caplog.records)
    for response in (missing, wrong):
        assert expected_token not in response.text
        assert supplied_token not in response.text
    assert expected_token not in emitted_text
    assert supplied_token not in emitted_text


def test_generate_session_token_returns_a_nonempty_url_safe_token():
    from research_agent.runtime.session import generate_session_token

    token = generate_session_token()

    assert token
    assert all(character.isalnum() or character in {"-", "_"} for character in token)

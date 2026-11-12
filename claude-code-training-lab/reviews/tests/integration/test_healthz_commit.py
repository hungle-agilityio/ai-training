import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

COMMIT = "5213e391e7ac164d86be3ee74e8a8c4eeba6ad1f"
ENV_NAME = "RENDER_GIT_COMMIT"


def test_healthz_carries_the_commit_header_when_the_variable_is_set(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_NAME, COMMIT)

    with CaptureQueriesContext(connection) as queries:
        response = Client().get("/healthz/")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert response["X-Commit"] == COMMIT
    assert len(queries) == 0


def test_healthz_stays_plain_text_with_the_commit_header(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_NAME, COMMIT)

    response = Client().get("/healthz/")

    assert response["Content-Type"].startswith("text/plain")


def test_healthz_strips_whitespace_from_the_commit_header(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_NAME, "abc\n")

    response = Client().get("/healthz/")

    assert response["X-Commit"] == "abc"


def test_healthz_has_no_commit_header_when_the_variable_is_missing(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_NAME, raising=False)

    with CaptureQueriesContext(connection) as queries:
        response = Client().get("/healthz/")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert "X-Commit" not in response
    assert len(queries) == 0


@pytest.mark.parametrize("blank", ["", "  ", "\t"])
def test_healthz_has_no_commit_header_when_the_variable_is_blank(
    db: None, monkeypatch: pytest.MonkeyPatch, blank: str
) -> None:
    monkeypatch.setenv(ENV_NAME, blank)

    with CaptureQueriesContext(connection) as queries:
        response = Client().get("/healthz/")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert "X-Commit" not in response
    assert len(queries) == 0


def test_healthz_reads_the_commit_variable_on_every_request(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = Client()
    monkeypatch.setenv(ENV_NAME, "first")
    first = client.get("/healthz/")

    monkeypatch.setenv(ENV_NAME, "second")
    second = client.get("/healthz/")

    assert first["X-Commit"] == "first"
    assert second["X-Commit"] == "second"

import io
import json
import urllib.error
from typing import Any

import pytest
from pytest_mock import MockerFixture

from reviews.claude_client import ClaudeError, create_message

KEY = "sk-secret-key"
TEXT = "private review text"


def call() -> str:
    return create_message(
        api_key=KEY, model="m", system="sys", user_text=TEXT, max_tokens=5, timeout=3
    )


def fake_response(mocker: MockerFixture, payload: bytes) -> Any:
    response = mocker.MagicMock()
    response.read.return_value = payload
    response.__enter__.return_value = response
    return mocker.patch("urllib.request.urlopen", return_value=response)


def test_request_url_headers_and_body(mocker: MockerFixture) -> None:
    answer = json.dumps({"content": [{"type": "text", "text": "hi"}]}).encode()
    urlopen = fake_response(mocker, answer)

    assert call() == "hi"

    request = urlopen.call_args.args[0]
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.get_method() == "POST"
    headers = {k.lower(): v for k, v in request.header_items()}
    assert headers["x-api-key"] == KEY
    assert headers["anthropic-version"] == "2023-06-01"
    assert headers["content-type"] == "application/json"
    assert json.loads(request.data) == {
        "model": "m",
        "max_tokens": 5,
        "system": "sys",
        "messages": [{"role": "user", "content": TEXT}],
    }
    assert urlopen.call_args.kwargs["timeout"] == 3


def test_text_blocks_are_joined(mocker: MockerFixture) -> None:
    blocks = [{"type": "text", "text": "a"}, {"type": "tool_use"}, {"type": "text", "text": "b"}]
    fake_response(mocker, json.dumps({"content": blocks}).encode())
    assert call() == "ab"


def test_http_error_keeps_only_kind_and_status(mocker: MockerFixture) -> None:
    error = urllib.error.HTTPError("u", 429, f"{KEY} {TEXT}", {}, io.BytesIO(b""))  # type: ignore[arg-type]
    mocker.patch("urllib.request.urlopen", side_effect=error)
    with pytest.raises(ClaudeError) as caught:
        call()
    assert caught.value.kind == "http_error"
    assert caught.value.status == 429
    assert str(caught.value) == "http_error 429"


@pytest.mark.parametrize(
    ("side_effect", "kind"),
    [
        (TimeoutError(), "timeout"),
        (urllib.error.URLError(KEY), "network_error"),
        (OSError(KEY), "network_error"),
    ],
)
def test_network_errors(mocker: MockerFixture, side_effect: Exception, kind: str) -> None:
    mocker.patch("urllib.request.urlopen", side_effect=side_effect)
    with pytest.raises(ClaudeError) as caught:
        call()
    assert str(caught.value) == f"{kind} -"
    assert KEY not in str(caught.value)


@pytest.mark.parametrize(
    ("payload", "kind"),
    [
        (b"not json", "invalid_json"),
        (b"[]", "empty_answer"),
        (b'{"content": []}', "empty_answer"),
        (b'{"content": [{"type": "text", "text": "  "}]}', "empty_answer"),
    ],
)
def test_bad_answers(mocker: MockerFixture, payload: bytes, kind: str) -> None:
    fake_response(mocker, payload)
    with pytest.raises(ClaudeError) as caught:
        call()
    assert caught.value.kind == kind

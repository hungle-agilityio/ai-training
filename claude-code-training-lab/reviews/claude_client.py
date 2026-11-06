import json
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class ClaudeError(Exception):
    """A failed call; holds only the error kind and the HTTP status, never a key or a text."""

    def __init__(self, kind: str, status: int | None = None) -> None:
        super().__init__(f"{kind} {status if status is not None else '-'}")
        self.kind = kind
        self.status = status


def create_message(
    *,
    api_key: str,
    model: str,
    system: str,
    user_text: str,
    max_tokens: int,
    timeout: float,
) -> str:
    """Send one message to Claude and return the joined text blocks of the answer."""
    body = json.dumps(
        {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_text}],
        }
    ).encode()
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        raise ClaudeError("http_error", error.code) from None
    except TimeoutError:
        raise ClaudeError("timeout") from None
    except OSError:
        raise ClaudeError("network_error") from None
    try:
        data: Any = json.loads(raw)
    except ValueError:
        raise ClaudeError("invalid_json") from None
    blocks = data.get("content") if isinstance(data, dict) else None
    texts = [
        block["text"]
        for block in (blocks if isinstance(blocks, list) else [])
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]
    text = "".join(texts)
    if not text.strip():
        raise ClaudeError("empty_answer")
    return text

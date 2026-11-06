import importlib
import logging
from collections.abc import Iterator
from typing import Any

import pytest
from django.test import override_settings
from pytest_mock import MockerFixture

import reviewradar.settings as project_settings
from reviews import reply_suggestion
from reviews.claude_client import ClaudeError
from reviews.models import Branch, Business, Review
from reviews.reply_service import clean_reply_text
from reviews.reply_suggestion import (
    FAKE_REPLY_TEXT,
    SUGGESTION_MAX_TOKENS,
    SUGGESTION_TIMEOUT_SECONDS,
    ReplySuggestion,
    suggest_reply,
    suggestion_mode,
)

REVIEW_TEXT = "The wait was far too long"
KEY = "sk-secret-key"
NO_AI = {"DEBUG": False, "ANTHROPIC_API_KEY": "", "REVIEWRADAR_AI_FAKE": False}
LIVE = {"DEBUG": False, "ANTHROPIC_API_KEY": KEY, "REVIEWRADAR_AI_FAKE": False}


@pytest.fixture
def review(db: None) -> Review:
    branch = Branch.objects.create(business=Business.objects.create(name="B"), name="Airport")
    return Review.objects.create(
        branch=branch, rating=2, text=REVIEW_TEXT, created_at="2026-11-01T00:00:00Z"
    )


@pytest.fixture
def fresh_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    yield lambda: importlib.reload(project_settings)
    monkeypatch.undo()
    importlib.reload(project_settings)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch, fresh_settings: Any) -> None:
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "REVIEWRADAR_AI_FAKE"):
        monkeypatch.delenv(name, raising=False)
    module = fresh_settings()
    assert module.ANTHROPIC_API_KEY == ""
    assert module.ANTHROPIC_MODEL == "claude-haiku-5-5"
    assert module.REVIEWRADAR_AI_FAKE is False


def test_settings_are_trimmed_and_fake_needs_exactly_one(
    monkeypatch: pytest.MonkeyPatch, fresh_settings: Any
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "  k  ")
    monkeypatch.setenv("ANTHROPIC_MODEL", "   ")
    monkeypatch.setenv("REVIEWRADAR_AI_FAKE", "true")
    module = fresh_settings()
    assert module.ANTHROPIC_API_KEY == "k"
    assert module.ANTHROPIC_MODEL == "claude-haiku-5-5"
    assert module.REVIEWRADAR_AI_FAKE is False
    monkeypatch.setenv("ANTHROPIC_MODEL", " my-model ")
    monkeypatch.setenv("REVIEWRADAR_AI_FAKE", "1")
    module = fresh_settings()
    assert module.ANTHROPIC_MODEL == "my-model"
    assert module.REVIEWRADAR_AI_FAKE is True


@pytest.mark.parametrize(
    ("debug", "key", "fake", "mode"),
    [
        (False, "", False, "off"),
        (True, "", False, "fake"),
        (False, "k", False, "live"),
        (True, "k", False, "live"),
        (False, "", True, "fake"),
        (False, "k", True, "fake"),
    ],
)
def test_mode(debug: bool, key: str, fake: bool, mode: str) -> None:
    with override_settings(DEBUG=debug, ANTHROPIC_API_KEY=key, REVIEWRADAR_AI_FAKE=fake):
        assert suggestion_mode() == mode


@pytest.mark.django_db
def test_unknown_review_gives_none() -> None:
    assert suggest_reply(999) is None


@override_settings(**NO_AI)
def test_off_makes_no_call(review: Review, mocker: MockerFixture) -> None:
    create = mocker.patch("reviews.claude_client.create_message")
    assert suggest_reply(review.id) == ReplySuggestion("off", "")
    create.assert_not_called()


@override_settings(DEBUG=False, ANTHROPIC_API_KEY="k", REVIEWRADAR_AI_FAKE=True)
def test_fake_returns_demo_draft_without_network(review: Review, mocker: MockerFixture) -> None:
    create = mocker.patch("reviews.claude_client.create_message")
    result = suggest_reply(review.id)
    assert result == ReplySuggestion("ok", f"{FAKE_REPLY_TEXT}\n\n— Airport team")
    create.assert_not_called()


@override_settings(**LIVE, ANTHROPIC_MODEL="mm")
def test_live_sends_four_lines_and_signs(review: Review, mocker: MockerFixture) -> None:
    create = mocker.patch("reviews.claude_client.create_message", return_value="  Sorry!\n ")
    result = suggest_reply(review.id)
    assert result == ReplySuggestion("ok", "Sorry!\n\n— Airport team")
    kwargs = create.call_args.kwargs
    assert kwargs["user_text"] == f"Location: Airport\nRating: 2 out of 5\nReview:\n{REVIEW_TEXT}"
    assert kwargs["model"] == "mm"
    assert kwargs["api_key"] == KEY
    assert kwargs["system"] == reply_suggestion.REPLY_SYSTEM_PROMPT
    assert kwargs["max_tokens"] == SUGGESTION_MAX_TOKENS == 500
    assert kwargs["timeout"] == SUGGESTION_TIMEOUT_SECONDS == 15


@override_settings(**LIVE)
def test_long_answer_is_cut_at_a_space(review: Review, mocker: MockerFixture) -> None:
    mocker.patch("reviews.claude_client.create_message", return_value="word " * 240)
    result = suggest_reply(review.id)
    assert result is not None
    assert len(result.draft) <= 1000
    assert result.draft.endswith("\n\n— Airport team")
    assert not result.draft.split("\n\n")[0].endswith(" ")
    assert clean_reply_text(result.draft) is not None


@override_settings(**LIVE)
def test_long_answer_without_spaces_is_cut(review: Review, mocker: MockerFixture) -> None:
    mocker.patch("reviews.claude_client.create_message", return_value="x" * 1200)
    result = suggest_reply(review.id)
    assert result is not None
    assert len(result.draft) <= 1000
    assert clean_reply_text(result.draft) is not None


@override_settings(**LIVE)
@pytest.mark.parametrize(
    ("error", "line"),
    [
        (ClaudeError("http_error", 500), "Reply suggestion failed: http_error 500"),
        (ClaudeError("timeout"), "Reply suggestion failed: timeout -"),
    ],
)
def test_failure_logs_one_safe_warning(
    review: Review,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    error: ClaudeError,
    line: str,
) -> None:
    create = mocker.patch("reviews.claude_client.create_message", side_effect=error)
    with caplog.at_level(logging.DEBUG):
        result = suggest_reply(review.id)
    assert result == ReplySuggestion("failed", "")
    assert create.call_count == 1
    messages = [r.getMessage() for r in caplog.records if r.name == "reviews.reply_suggestion"]
    assert messages == [line]
    assert all(
        REVIEW_TEXT not in r.getMessage() and KEY not in r.getMessage() for r in caplog.records
    )


@override_settings(**LIVE)
def test_empty_answer_fails(review: Review, mocker: MockerFixture) -> None:
    mocker.patch("reviews.claude_client.create_message", return_value="  ")
    assert suggest_reply(review.id) == ReplySuggestion("failed", "")


@override_settings(**NO_AI)
def test_one_query(review: Review, django_assert_num_queries: Any) -> None:
    with django_assert_num_queries(1):
        suggest_reply(review.id)

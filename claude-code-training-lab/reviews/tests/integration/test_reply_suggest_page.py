from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews import reply_suggestion
from reviews.models import Branch, Business, Review, ReviewReply
from reviews.reply_suggestion import ReplySuggestion

NOW = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)
DRAFT = "Sorry about the wait.\n\n— Clinic A team"
OK_NOTE = "Suggested by Claude. Read and edit it before you save."
FAILED_NOTE = "Could not get a suggestion right now. Try again or write your own."
INVALID_NOTE = "Write a reply of 1 to 1,000 characters."
BUTTON = '<button type="submit" name="action" value="suggest" id="suggest-reply" formnovalidate'


@pytest.fixture
def review(db: None) -> Review:
    branch = Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")
    return Review.objects.create(
        branch=branch, rating=2, text="Waited an hour.", created_at=NOW - timedelta(days=2)
    )


def url(review: Review) -> str:
    return f"/reviews/{review.id}/reply/"


def set_mode(mocker: MockerFixture, mode: str) -> None:
    mocker.patch.object(reply_suggestion, "suggestion_mode", return_value=mode)


def stub(mocker: MockerFixture, status: str, draft: str = "") -> MagicMock:
    suggestion = ReplySuggestion(status, draft)  # type: ignore[arg-type]
    return mocker.patch.object(reply_suggestion, "suggest_reply", return_value=suggestion)


@pytest.mark.parametrize("mode", ["fake", "live"])
def test_button_and_hint_shown_when_suggestions_are_on(
    review: Review, mocker: MockerFixture, mode: str
) -> None:
    set_mode(mocker, mode)
    page = Client().get(url(review)).content.decode()
    assert BUTTON in page
    assert "Suggest a reply" in page
    assert 'id="suggest-hint"' in page
    assert "Claude writes a draft in the box. Nothing is saved until you press Save reply." in page
    assert page.index("Save reply</button>") < page.index(BUTTON)


def test_no_button_when_suggestions_are_off(review: Review, mocker: MockerFixture) -> None:
    set_mode(mocker, "off")
    page = Client().get(url(review)).content.decode()
    assert "suggest-reply" not in page
    assert "suggest-hint" not in page


def test_suggest_ok_fills_box_and_saves_nothing(review: Review, mocker: MockerFixture) -> None:
    set_mode(mocker, "fake")
    stub(mocker, "ok", DRAFT)
    response = Client().post(url(review), {"action": "suggest", "text": "typed"})
    page = response.content.decode()
    assert response.status_code == 200
    assert "Sorry about the wait." in page
    assert "typed" not in page
    assert 'role="status"' in page
    assert "suggest-note" in page
    assert OK_NOTE in page
    assert INVALID_NOTE not in page
    assert not ReviewReply.objects.exists()


def test_suggest_ok_keeps_saved_reply_and_last_saved(review: Review, mocker: MockerFixture) -> None:
    ReviewReply.objects.create(review=review, text="Old reply", created_at=NOW, updated_at=NOW)
    set_mode(mocker, "fake")
    stub(mocker, "ok", DRAFT)
    page = Client().post(url(review), {"action": "suggest", "text": ""}).content.decode()
    assert "Last saved" in page
    assert ReviewReply.objects.get(review=review).text == "Old reply"


def test_suggest_failed_shows_alert_and_keeps_typed_text(
    review: Review, mocker: MockerFixture
) -> None:
    set_mode(mocker, "live")
    stub(mocker, "failed")
    response = Client().post(url(review), {"action": "suggest", "text": "my words"})
    page = response.content.decode()
    assert response.status_code == 200
    assert FAILED_NOTE in page
    assert 'class="alert"' in page
    assert "my words" in page
    assert INVALID_NOTE not in page
    assert OK_NOTE not in page
    assert not ReviewReply.objects.exists()


def test_suggest_off_keeps_typed_text_without_message(
    review: Review, mocker: MockerFixture
) -> None:
    set_mode(mocker, "off")
    stub(mocker, "off")
    page = Client().post(url(review), {"action": "suggest", "text": "my words"}).content.decode()
    assert "my words" in page
    assert FAILED_NOTE not in page
    assert OK_NOTE not in page
    assert INVALID_NOTE not in page


def test_suggest_with_empty_box_is_not_invalid(review: Review, mocker: MockerFixture) -> None:
    set_mode(mocker, "live")
    stub(mocker, "failed")
    page = Client().post(url(review), {"action": "suggest", "text": ""}).content.decode()
    assert INVALID_NOTE not in page


@pytest.mark.parametrize("data", [{"text": "Thanks"}, {"action": "save", "text": "Thanks"}])
def test_other_action_saves_and_never_asks_claude(
    review: Review, mocker: MockerFixture, data: dict[str, str]
) -> None:
    spy = stub(mocker, "ok", DRAFT)
    response = Client().post(url(review), data)
    assert response.status_code == 302
    assert ReviewReply.objects.get(review=review).text == "Thanks"
    spy.assert_not_called()


def test_suggest_for_unknown_review_answers_404(db: None, mocker: MockerFixture) -> None:
    set_mode(mocker, "fake")
    assert Client().post("/reviews/999/reply/", {"action": "suggest"}).status_code == 404


def test_suggest_without_csrf_token_answers_403(review: Review, mocker: MockerFixture) -> None:
    spy = stub(mocker, "ok", DRAFT)
    client = Client(enforce_csrf_checks=True)
    assert client.post(url(review), {"action": "suggest"}).status_code == 403
    spy.assert_not_called()


def test_suggest_makes_at_most_two_queries_and_one_call(
    review: Review, mocker: MockerFixture, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    set_mode(mocker, "live")
    create = mocker.patch(
        "reviews.reply_suggestion.claude_client.create_message", return_value="Thanks."
    )
    with django_assert_max_num_queries(2):
        response = Client().post(url(review), {"action": "suggest", "text": ""})
    assert response.status_code == 200
    assert create.call_count == 1


def test_get_makes_no_call(review: Review, mocker: MockerFixture) -> None:
    set_mode(mocker, "live")
    create = mocker.patch("reviews.reply_suggestion.claude_client.create_message")
    Client().get(url(review))
    create.assert_not_called()


def test_new_styles_live_in_replies_css() -> None:
    text = (Path(__file__).parents[2] / "static/reviews/replies.css").read_text()
    assert "#suggest-reply" in text
    assert "suggest-note" in text


@pytest.mark.login
def test_signed_out_post_goes_to_login_and_makes_no_call(
    review: Review, mocker: MockerFixture
) -> None:
    create = mocker.patch("reviews.reply_suggestion.claude_client.create_message")
    response = Client().post(url(review), {"action": "suggest"})
    assert response.status_code == 302
    assert response["Location"] == f"/login/?next={url(review)}"
    create.assert_not_called()

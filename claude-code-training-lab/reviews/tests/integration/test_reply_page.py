from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review, ReviewReply

NOW = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


@pytest.fixture
def review(branch: Branch) -> Review:
    return Review.objects.create(
        branch=branch, rating=2, text="Waited an hour.", created_at=NOW - timedelta(days=2)
    )


def url(review: Review) -> str:
    return f"/reviews/{review.id}/reply/"


def test_unknown_review_answers_404(db: None) -> None:
    assert Client().get("/reviews/999/reply/").status_code == 404
    assert Client().post("/reviews/999/reply/", {"text": "Thanks"}).status_code == 404


@pytest.mark.parametrize("method", ["put", "delete", "patch"])
def test_other_methods_answer_405(review: Review, method: str) -> None:
    assert getattr(Client(), method)(url(review)).status_code == 405


def test_get_shows_review_and_empty_form(review: Review) -> None:
    response = Client().get(url(review))
    page = response.content.decode()
    assert response.status_code == 200
    assert "<title>Reply to a review · ReviewRadar</title>" in page
    assert "<h1>Reply to a review</h1>" in page
    assert "Write the reply your team will post." in page
    assert "Export JSON" not in page
    assert f'href="/locations/{review.branch_id}/"' in page
    assert 'aria-label="2 out of 5"' in page
    assert "Nov 3, 2026" in page
    assert 'data-sensitive="review-text"' in page
    assert "Waited an hour." in page
    assert 'class="nav-item is-active" href="/replies/" aria-current="page"' in page
    assert 'id="reply-form"' in page
    assert 'method="post"' in page
    assert "csrfmiddlewaretoken" in page
    assert 'id="reply-text"' in page
    assert 'name="text"' in page
    assert 'maxlength="1000"' in page
    assert "required" in page
    assert 'data-sensitive="reply-text"' in page
    assert "Your reply" in page
    assert "Up to 1,000 characters." in page
    assert "Save reply" in page
    assert 'href="/replies/"' in page
    assert "Back to reply drafts" in page
    assert "Last saved" not in page


def test_get_with_reply_shows_text_and_last_saved_by_user(review: Review) -> None:
    user = get_user_model().objects.create_user(username="anna", password="x")
    ReviewReply.objects.create(
        review=review, text="Sorry!", replied_by=user, created_at=NOW, updated_at=NOW
    )
    page = Client().get(url(review)).content.decode()
    assert "Sorry!</textarea>" in page
    assert "Last saved Nov 5, 2026, 17:00 by" in page
    assert "<span data-sensitive>anna</span>" in page


def test_get_with_reply_of_deleted_user_has_no_by(review: Review) -> None:
    ReviewReply.objects.create(review=review, text="Sorry!", created_at=NOW, updated_at=NOW)
    page = Client().get(url(review)).content.decode()
    line = page.split("Last saved")[1].split("</p>")[0]
    assert line.strip() == "Nov 5, 2026, 17:00"


def test_valid_post_saves_and_redirects(review: Review) -> None:
    user = get_user_model().objects.create_user(username="anna", password="x")
    client = Client()
    client.force_login(user)
    response = client.post(url(review), {"text": "  Thank you  "})
    assert response.status_code == 302
    assert response["Location"] == "/replies/?saved=1"
    reply = ReviewReply.objects.get(review=review)
    assert reply.text == "Thank you"
    assert reply.replied_by == user
    page = client.get("/replies/?saved=1").content.decode()
    assert 'role="status"' in page
    assert "Reply saved." in page
    assert "Waited an hour." not in page


def test_post_updates_existing_reply_and_counts_line_break_once(review: Review) -> None:
    ReviewReply.objects.create(review=review, text="Old", created_at=NOW, updated_at=NOW)
    text = "a\r\n" * 400 + "b"  # 1,201 characters with CRLF, 801 as the browser counts them
    assert Client().post(url(review), {"text": text}).status_code == 302
    reply = ReviewReply.objects.get(review=review)
    assert reply.text.startswith("a\na")
    assert reply.created_at == NOW


def test_post_without_user_saves_none(review: Review) -> None:
    assert Client().post(url(review), {"text": "Thanks"}).status_code == 302
    assert ReviewReply.objects.get(review=review).replied_by is None


@pytest.mark.parametrize("query", ["", "?saved=2", "?saved=yes", "?saved="])
def test_saved_line_only_for_saved_1(db: None, query: str) -> None:
    assert "Reply saved." not in Client().get("/replies/" + query).content.decode()
    assert "Reply saved." in Client().get("/replies/?saved=1").content.decode()


@pytest.mark.parametrize("text", ["", "   ", "x" * 1001, "   " + "x" * 1001])
def test_invalid_post_shows_error_and_saves_nothing(review: Review, text: str) -> None:
    response = Client().post(url(review), {"text": text})
    page = response.content.decode()
    assert response.status_code == 200
    assert '<p class="alert">Write a reply of 1 to 1,000 characters.</p>' in page
    assert "Waited an hour." in page
    assert not ReviewReply.objects.exists()


def test_invalid_post_keeps_typed_text(review: Review) -> None:
    page = Client().post(url(review), {"text": "<b>" + "x" * 1001}).content.decode()
    assert "&lt;b&gt;" + "x" * 1001 + "</textarea>" in page


def test_post_without_csrf_token_answers_403(review: Review) -> None:
    client = Client(enforce_csrf_checks=True)
    assert client.post(url(review), {"text": "Thanks"}).status_code == 403
    assert not ReviewReply.objects.exists()


def test_replies_list_has_reply_button_column(review: Review) -> None:
    page = Client().get("/replies/").content.decode()
    assert '<th scope="col">Reply</th>' in page
    assert f'href="/reviews/{review.id}/reply/"' in page
    assert ">Reply</a>" in page


def test_get_makes_one_query(
    review: Review, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(1):
        Client().get(url(review))


def test_valid_post_makes_at_most_four_queries(
    review: Review, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(4):
        Client().post(url(review), {"text": "Thanks"})


@pytest.mark.login
def test_signed_out_visitor_goes_to_login(review: Review) -> None:
    response = Client().get(url(review))
    assert response.status_code == 302
    assert response["Location"] == f"/login/?next={url(review)}"

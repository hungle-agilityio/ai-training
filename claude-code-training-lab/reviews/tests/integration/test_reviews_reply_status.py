from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review, ReviewReply
from reviews.services import REVIEWS_PER_PAGE

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def _setup(replied: int = 2, open_: int = 3) -> tuple[list[Review], list[Review]]:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Hanoi")
    done = [
        Review.objects.create(branch=branch, rating=5, text=f"done {i}", created_at=NOW)
        for i in range(replied)
    ]
    todo = [
        Review.objects.create(branch=branch, rating=2, text=f"todo {i}", created_at=NOW)
        for i in range(open_)
    ]
    for review in done:
        ReviewReply.objects.create(review=review, text="Thanks", created_at=NOW, updated_at=NOW)
    return done, todo


@pytest.mark.django_db
def test_reviews_page_shows_reply_status_and_link_per_row() -> None:
    done, todo = _setup(1, 1)

    content = Client().get("/reviews/").content.decode()

    assert '<th scope="col">Reply</th>' in content
    assert 'class="reply-status reply-done"' in content
    assert 'class="reply-status reply-open"' in content
    assert f'href="/reviews/{done[0].id}/reply/">Edit reply</a>' in content
    assert f'href="/reviews/{todo[0].id}/reply/">Reply</a>' in content


@pytest.mark.django_db
def test_reply_filter_has_three_choices() -> None:
    _setup()

    content = Client().get("/reviews/").content.decode()

    assert 'id="filter-reply" name="reply"' in content
    assert '<option value="" selected>All</option>' in content
    assert '<option value="yes">Replied</option>' in content
    assert '<option value="no">Not replied</option>' in content


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("value", "shown", "hidden"), [("yes", "done", "todo"), ("no", "todo", "done")]
)
def test_reply_filter_keeps_only_matching_reviews(value: str, shown: str, hidden: str) -> None:
    _setup()

    content = Client().get("/reviews/", {"reply": value}).content.decode()

    assert f"{shown} 0" in content
    assert f"{hidden} 0" not in content
    assert f'<option value="{value}" selected>' in content


@pytest.mark.django_db
def test_wrong_reply_value_is_ignored_and_other_filters_apply() -> None:
    _setup()

    content = Client().get("/reviews/", {"reply": "maybe", "rating": "bad"}).content.decode()

    assert "todo 0" in content
    assert "done 0" not in content
    assert "reply=maybe" not in content


@pytest.mark.django_db
def test_reply_filter_is_kept_in_pager_export_and_cleared_by_clear() -> None:
    _setup(0, REVIEWS_PER_PAGE + 1)

    content = Client().get("/reviews/", {"reply": "no"}).content.decode()

    assert "?reply=no&amp;page=2" in content or "?reply=no&page=2" in content
    assert "/reviews/export/?reply=no" in content
    assert 'href="/reviews/">Clear</a>' in content


@pytest.mark.django_db
def test_csv_export_follows_reply_filter_with_same_columns() -> None:
    _setup()

    response = Client().get("/reviews/export/", {"reply": "yes"})
    body = b"".join(response.streaming_content).decode()  # type: ignore[attr-defined]

    assert "done 0" in body
    assert "todo 0" not in body
    assert body.splitlines()[0].lstrip("﻿") == "Location,Rating,Review text,Date"


@pytest.mark.django_db
def test_reviews_page_and_export_query_counts_do_not_grow(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    _setup(5, 5)

    with django_assert_max_num_queries(3):
        Client().get("/reviews/", {"reply": "no"})
    with django_assert_max_num_queries(3):
        response = Client().get("/reviews/export/", {"reply": "no"})
        b"".join(response.streaming_content)  # type: ignore[attr-defined]


@pytest.mark.django_db
def test_dashboard_and_location_page_query_counts_do_not_grow(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    _setup(3, 3)
    branch_id = Branch.objects.get().id

    with django_assert_max_num_queries(3):
        Client().get("/dashboard/")
    with django_assert_max_num_queries(4):
        Client().get(f"/locations/{branch_id}/")

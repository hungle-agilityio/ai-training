from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from reviews import reply_repository
from reviews.models import Branch, Business, Review, ReviewReply
from reviews.reply_service import replies_page
from reviews.services import REVIEWS_PER_PAGE

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


def add(branch: Branch, rating: int, age: timedelta, replied: bool = False) -> Review:
    review = Review.objects.create(branch=branch, rating=rating, text="Text", created_at=NOW - age)
    if replied:
        ReviewReply.objects.create(review=review, text="Thanks", created_at=NOW, updated_at=NOW)
    return review


def test_overdue_only_boundaries_ratings_and_replies(branch: Branch) -> None:
    older = add(branch, 1, timedelta(hours=24, seconds=1))
    exact = add(branch, 1, timedelta(hours=24))
    add(branch, 1, timedelta(hours=23, minutes=59, seconds=59))
    three = add(branch, 3, timedelta(days=5))
    add(branch, 2, timedelta(days=5), replied=True)
    two = add(branch, 2, timedelta(days=2))
    ids = [r.id for r in reply_repository.reviews_without_reply(overdue_only=True, now=NOW)]
    assert ids == [two.id, older.id]
    assert exact.id not in ids
    assert three.id not in ids


def test_overdue_only_keeps_order_oldest_first_then_lowest_id(branch: Branch) -> None:
    age = timedelta(days=2)
    first = add(branch, 2, age)
    second = add(branch, 1, age)
    oldest = add(branch, 1, timedelta(days=4))
    result = reply_repository.reviews_without_reply(overdue_only=True, now=NOW)
    assert [r.id for r in result] == [oldest.id, first.id, second.id]


def test_without_arguments_returns_everything_as_before(branch: Branch) -> None:
    fresh = add(branch, 1, timedelta(hours=1))
    five = add(branch, 5, timedelta(days=9))
    three = add(branch, 3, timedelta(days=9))
    add(branch, 1, timedelta(days=9), replied=True)
    result = reply_repository.reviews_without_reply()
    assert [r.id for r in result] == [fresh.id, three.id, five.id]


def test_rows_have_bool_is_overdue(branch: Branch) -> None:
    overdue = add(branch, 1, timedelta(days=2))
    fresh = add(branch, 1, timedelta(hours=1))
    page = replies_page(1, now=NOW)
    flags = {row.review_id: row.is_overdue for row in page.rows}
    assert flags == {overdue.id: True, fresh.id: False}
    assert all(type(row.is_overdue) is bool for row in page.rows)


def test_overdue_only_page_lists_only_overdue_rows(branch: Branch) -> None:
    overdue = add(branch, 1, timedelta(days=2))
    add(branch, 1, timedelta(hours=1))
    page = replies_page(1, overdue_only=True, now=NOW)
    assert [row.review_id for row in page.rows] == [overdue.id]
    assert page.overdue_only is True
    assert page.total == 1


def test_default_page_is_not_overdue_only_and_links_unchanged(branch: Branch) -> None:
    for _ in range(REVIEWS_PER_PAGE + 1):
        add(branch, 1, timedelta(days=2))
    page = replies_page(1, now=NOW)
    assert page.overdue_only is False
    assert page.next_href == "?page=2"
    assert [link.href for link in page.links if link.number] == ["?page=1", "?page=2"]


def test_overdue_only_links_keep_overdue_param(branch: Branch) -> None:
    for _ in range(REVIEWS_PER_PAGE + 1):
        add(branch, 1, timedelta(days=2))
    page = replies_page(2, overdue_only=True, now=NOW)
    assert page.overdue_only is True
    assert page.previous_href == "?overdue=1&page=1"
    assert page.next_href == "?overdue=1&page=2"
    assert [link.href for link in page.links if link.number] == [
        "?overdue=1&page=1",
        "?overdue=1&page=2",
    ]


def test_one_page_takes_at_most_two_queries(
    branch: Branch, django_assert_max_num_queries: Any
) -> None:
    for _ in range(3):
        add(branch, 1, timedelta(days=2))
    with django_assert_max_num_queries(2):
        page = replies_page(1, overdue_only=True, now=NOW)
        assert len(page.rows) == 3

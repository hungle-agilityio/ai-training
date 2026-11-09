from datetime import UTC, datetime, timedelta

import pytest

from reviews.reply_service import is_overdue

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (timedelta(hours=23, minutes=59, seconds=59), False),
        (timedelta(hours=24), False),
        (timedelta(hours=24, seconds=1), True),
    ],
)
def test_overdue_only_after_24_hours(age: timedelta, expected: bool) -> None:
    assert is_overdue(rating=1, has_reply=False, created_at=NOW - age, now=NOW) is expected


@pytest.mark.parametrize(("rating", "expected"), [(1, True), (2, True), (3, False), (5, False)])
def test_only_bad_ratings_are_overdue(rating: int, expected: bool) -> None:
    created = NOW - timedelta(days=3)
    assert is_overdue(rating=rating, has_reply=False, created_at=created, now=NOW) is expected


def test_bad_review_with_reply_is_never_overdue() -> None:
    created = NOW - timedelta(days=30)
    assert is_overdue(rating=1, has_reply=True, created_at=created, now=NOW) is False

from datetime import UTC, datetime, timedelta

import pytest

from reviews.templatetags.review_dates import full_review_date, relative_review_date

NOW = datetime(2026, 10, 29, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (timedelta(seconds=0), "just now"),
        (timedelta(seconds=59), "just now"),
        (timedelta(minutes=1), "1 minute ago"),
        (timedelta(minutes=1, seconds=59), "1 minute ago"),
        (timedelta(minutes=2), "2 minutes ago"),
        (timedelta(minutes=59, seconds=59), "59 minutes ago"),
        (timedelta(hours=1), "1 hour ago"),
        (timedelta(hours=1, minutes=59), "1 hour ago"),
        (timedelta(hours=23, minutes=59), "23 hours ago"),
        (timedelta(hours=24), "1 day ago"),
        (timedelta(days=2, hours=5), "2 days ago"),
        (timedelta(days=6, hours=23), "6 days ago"),
        (timedelta(days=7), "Oct 22, 2026"),
        (timedelta(days=10), "Oct 19, 2026"),
        (timedelta(hours=-3), "just now"),
    ],
)
def test_relative_text_follows_the_age(age: timedelta, expected: str) -> None:
    assert relative_review_date(NOW - age, NOW) == expected


def test_old_date_uses_vietnam_time_across_midnight_utc() -> None:
    written = datetime(2026, 10, 20, 18, 30, tzinfo=UTC)  # 01:30 on Oct 21 in Vietnam

    assert relative_review_date(written, NOW) == "Oct 21, 2026"


def test_full_date_is_vietnam_time_24_hour_without_seconds() -> None:
    written = datetime(2026, 10, 26, 7, 5, 42, tzinfo=UTC)

    assert full_review_date(written) == "Oct 26, 2026, 14:05"


def test_full_date_crosses_midnight_utc() -> None:
    assert full_review_date(datetime(2026, 10, 26, 18, 0, tzinfo=UTC)) == "Oct 27, 2026, 01:00"

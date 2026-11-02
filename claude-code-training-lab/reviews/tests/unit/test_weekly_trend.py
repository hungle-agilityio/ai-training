from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from reviews.models import Branch, Business, Review
from reviews.trend_service import TREND_WEEKS, WeekPoint, weekly_trend

VN = ZoneInfo("Asia/Ho_Chi_Minh")
# Wednesday 28 October 2026, Vietnam time: the week of Monday 26 October
NOW = datetime(2026, 10, 28, 12, 0, tzinfo=VN)


def _add(branch: Branch, rating: int, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text="ok", created_at=created_at)


@pytest.fixture
def branch() -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")


@pytest.mark.django_db
def test_returns_eight_weeks_oldest_first_ending_with_current_week(branch: Branch) -> None:
    points = weekly_trend(branch.id, NOW)

    assert TREND_WEEKS == 8
    assert len(points) == 8
    assert points[-1].monday == date(2026, 10, 26)
    assert points[0].monday == date(2026, 9, 7)
    assert [p.monday for p in points] == sorted(p.monday for p in points)
    assert points[-1].label == "Oct 26"
    assert points[0].label == "Sep 7"
    assert isinstance(points[0], WeekPoint)


@pytest.mark.django_db
def test_current_week_uses_vietnam_time_whatever_time_zone_is_active(branch: Branch) -> None:
    # Sunday 25 Oct 20:00 UTC is Monday 26 Oct 03:00 in Vietnam
    now = datetime(2026, 10, 25, 20, 0, tzinfo=UTC)
    with timezone.override(ZoneInfo("America/Los_Angeles")):
        points = weekly_trend(branch.id, now)

    assert points[-1].monday == date(2026, 10, 26)


@pytest.mark.django_db
def test_sunday_night_counts_in_that_week_and_monday_midnight_in_the_next(branch: Branch) -> None:
    _add(branch, 5, datetime(2026, 10, 25, 23, 59, tzinfo=VN))
    _add(branch, 1, datetime(2026, 10, 26, 0, 0, tzinfo=VN))

    points = weekly_trend(branch.id, NOW)

    assert (points[-2].review_count, points[-2].average_rating) == (1, 5.0)
    assert (points[-1].review_count, points[-1].average_rating) == (1, 1.0)


@pytest.mark.django_db
def test_week_edge_is_read_in_vietnam_time_when_another_zone_is_active(branch: Branch) -> None:
    # 17:00 UTC Sunday is Monday 00:00 in Vietnam
    _add(branch, 4, datetime(2026, 10, 25, 17, 0, tzinfo=UTC))
    with timezone.override(ZoneInfo("America/Los_Angeles")):
        points = weekly_trend(branch.id, NOW)

    assert points[-1].review_count == 1
    assert points[-2].review_count == 0


@pytest.mark.django_db
def test_average_rounds_half_up_to_one_decimal(branch: Branch) -> None:
    for rating in (5, 2, 4, 2):
        _add(branch, rating, datetime(2026, 10, 27, 10, 0, tzinfo=VN))

    last = weekly_trend(branch.id, NOW)[-1]

    assert last.review_count == 4
    assert last.average_rating == 3.3
    assert isinstance(last.average_rating, float)
    assert last.bar_percent == 66
    assert isinstance(last.bar_percent, int)


@pytest.mark.django_db
def test_empty_week_has_no_average_and_no_bar(branch: Branch) -> None:
    first = weekly_trend(branch.id, NOW)[0]

    assert first.review_count == 0
    assert first.average_rating is None
    assert first.bar_percent == 0


@pytest.mark.django_db
def test_other_locations_and_out_of_window_reviews_are_not_counted(branch: Branch) -> None:
    other = Branch.objects.create(business=branch.business, name="Other")
    _add(other, 1, datetime(2026, 10, 27, 10, 0, tzinfo=VN))
    _add(branch, 1, datetime(2026, 9, 6, 23, 59, tzinfo=VN))  # before the first Monday
    _add(branch, 1, datetime(2026, 11, 2, 0, 0, tzinfo=VN))  # next Monday
    _add(branch, 3, datetime(2026, 9, 7, 0, 0, tzinfo=VN))  # first moment of the window

    points = weekly_trend(branch.id, NOW)

    assert sum(p.review_count for p in points) == 1
    assert points[0].review_count == 1
    assert points[-1].review_count == 0

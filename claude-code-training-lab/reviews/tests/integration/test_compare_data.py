from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews import compare_service
from reviews.models import Branch, Business, Review


def seed() -> dict[str, int]:
    call_command("seed_demo_data", stdout=StringIO())
    return {b.name: b.id for b in Branch.objects.all()}


def stars(side: compare_service.LocationSide) -> list[tuple[int, int, int]]:
    return [(r.stars, r.count, r.percent) for r in side.star_rows]


@pytest.mark.django_db
def test_demo_data_all_time(django_assert_num_queries: DjangoAssertNumQueries) -> None:
    ids = seed()
    now = timezone.now()

    with django_assert_num_queries(1):
        result = compare_service.compare_locations(ids["Downtown"], ids["Riverside"], None, now)

    assert result is not None
    assert (result.a.review_count, result.a.average_rating) == (5, 4.0)
    assert (result.a.good_percent, result.a.bad_percent) == (60, 0)
    assert result.a.replied_in_time_percent is None
    assert stars(result.a) == [(5, 2, 40), (4, 1, 20), (3, 2, 40), (2, 0, 0), (1, 0, 0)]
    assert (result.b.review_count, result.b.average_rating) == (5, 3.4)
    assert (result.b.good_percent, result.b.bad_percent) == (60, 40)
    assert result.b.replied_in_time_percent == 100
    assert stars(result.b) == [(5, 1, 20), (4, 2, 40), (3, 0, 0), (2, 2, 40), (1, 0, 0)]
    assert result.difference == 0.6
    assert isinstance(result.b.average_rating, float)
    assert isinstance(result.b.replied_in_time_percent, int)


@pytest.mark.django_db
def test_demo_data_airport_has_slow_replies() -> None:
    ids = seed()

    result = compare_service.compare_locations(
        ids["Airport"], ids["Downtown"], None, timezone.now()
    )

    assert result is not None
    assert result.a.review_count == 4
    assert result.a.average_rating == 2.0
    assert (result.a.good_percent, result.a.bad_percent) == (0, 75)
    assert result.a.replied_in_time_percent == 0


@pytest.mark.django_db
def test_demo_data_last_30_days() -> None:
    ids = seed()

    result = compare_service.compare_locations(
        ids["Downtown"], ids["Riverside"], 30, timezone.now()
    )

    assert result is not None
    assert (result.a.review_count, result.a.average_rating) == (2, 4.5)
    assert (result.b.review_count, result.b.average_rating) == (2, 4.5)
    assert result.difference == 0.0
    assert result.period_label == "Last 30 days"


@pytest.mark.django_db
def test_location_without_review_in_period_still_comes_back_with_zeros() -> None:
    business = Business.objects.create(name="B")
    quiet = Branch.objects.create(business=business, name="Quiet")
    busy = Branch.objects.create(business=business, name="Busy")
    now = timezone.now()
    Review.objects.create(branch=busy, rating=5, text="t", created_at=now - timedelta(days=1))
    Review.objects.create(branch=quiet, rating=1, text="t", created_at=now - timedelta(days=200))

    result = compare_service.compare_locations(quiet.id, busy.id, 30, now)

    assert result is not None
    assert result.a.review_count == 0
    assert result.a.average_rating is None
    assert result.a.replied_in_time_percent is None
    assert result.difference is None


@pytest.mark.django_db
def test_unknown_or_same_location_gives_none() -> None:
    ids = seed()
    now = timezone.now()

    assert compare_service.compare_locations(ids["Downtown"], 99999, None, now) is None
    assert compare_service.compare_locations(ids["Downtown"], ids["Downtown"], None, now) is None

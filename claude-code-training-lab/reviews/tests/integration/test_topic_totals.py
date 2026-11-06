from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from django.core.management import call_command
from django.utils import timezone

from reviews import topic_repository, topic_service
from reviews.models import Branch, Business, Review
from reviews.repositories import create_review

pytestmark = pytest.mark.django_db


@pytest.fixture
def demo() -> None:
    call_command("seed_demo_data")


@pytest.fixture
def branch() -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="B"), name="A")


def row_of(overview: topic_service.TopicOverview, label: str) -> topic_service.TopicRow:
    return next(row for row in overview.rows if row.label == label)


def test_demo_overview_matches_the_spec(demo: None) -> None:
    overview = topic_service.topic_overview(None, None, timezone.now())
    assert (overview.review_count, overview.no_topic_count) == (14, 1)
    got = [
        (r.label, r.review_count, r.share_percent, r.bad_count, r.bad_percent, r.average_rating)
        for r in overview.rows
    ]
    assert got == [
        ("Doctor & treatment", 4, 29, 0, 0, 4.0),
        ("Staff", 4, 29, 2, 50, 3.5),
        ("Wait time", 4, 29, 2, 50, 2.5),
        ("Booking & phone", 2, 14, 2, 100, 1.5),
        ("Parking", 2, 14, 0, 0, 3.5),
        ("Price & billing", 2, 14, 1, 50, 2.0),
        ("Cleanliness", 1, 7, 0, 0, 4.0),
    ]


def test_number_types(demo: None) -> None:
    overview = topic_service.topic_overview(None, None, timezone.now())
    assert type(overview.review_count) is int
    for row in overview.rows:
        assert type(row.review_count) is int
        assert type(row.share_percent) is int
        assert type(row.bad_percent) is int
        assert type(row.average_rating) is float


def test_location_topics_for_airport(demo: None) -> None:
    airport = Branch.objects.get(name="Airport")
    got = [
        (t.label, t.review_count, t.bad_count) for t in topic_service.location_topics(airport.pk)
    ]
    assert got == [("Wait time", 3, 2), ("Booking & phone", 1, 1), ("Doctor & treatment", 1, 0)]


def test_topic_with_no_reviews_is_zero_and_average_none(branch: Branch) -> None:
    create_review(branch=branch, rating=4, text="Clean", created_at=timezone.now())
    overview = topic_service.topic_overview(None, None, timezone.now())
    staff = row_of(overview, "Staff")
    assert (staff.review_count, staff.share_percent, staff.average_rating) == (0, 0, None)
    assert overview.rows[0].label == "Cleanliness"


def test_review_with_two_topics_counts_in_both(branch: Branch) -> None:
    create_review(branch=branch, rating=1, text="slow staff", created_at=timezone.now())
    overview = topic_service.topic_overview(None, None, timezone.now())
    assert row_of(overview, "Wait time").review_count == 1
    assert row_of(overview, "Staff").review_count == 1
    assert (overview.review_count, overview.no_topic_count) == (1, 0)


def test_period_boundary_is_inclusive(branch: Branch) -> None:
    now = timezone.now()
    create_review(branch=branch, rating=3, text="slow", created_at=now - timedelta(days=30))
    late = now - timedelta(days=30, seconds=1)
    create_review(branch=branch, rating=3, text="slow", created_at=late)
    assert topic_service.topic_overview(None, 30, now).review_count == 1
    assert topic_service.topic_overview(None, None, now).review_count == 2


def test_month_topics_change_and_filter(branch: Branch) -> None:
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 11, 1, tzinfo=UTC)
    previous = datetime(2026, 9, 1, tzinfo=UTC)
    create_review(branch=branch, rating=1, text="slow", created_at=start)
    create_review(branch=branch, rating=5, text="slow", created_at=start + timedelta(days=1))
    create_review(branch=branch, rating=5, text="slow", created_at=previous)
    create_review(branch=branch, rating=5, text="clean", created_at=previous)
    create_review(branch=branch, rating=5, text="clean", created_at=end)
    months = topic_service.month_topics(start, end, previous)
    got = [(t.label, t.review_count, t.bad_count, t.change) for t in months]
    assert got == [("Wait time", 2, 1, 1), ("Cleanliness", 0, 0, -1)]


def test_percent_rounds_half_up() -> None:
    assert topic_service.percent(1, 8) == 13
    assert topic_service.percent(0, 0) == 0


def bulk() -> int:
    business = Business.objects.create(name="B")
    branches = Branch.objects.bulk_create(
        [Branch(business=business, name="L" + str(i)) for i in range(200)]
    )
    now = timezone.now()
    Review.objects.bulk_create(
        [
            Review(
                branch=branches[i % 200],
                rating=i % 5 + 1,
                text="slow staff",
                search_text="slow staff",
                created_at=now,
            )
            for i in range(500)
        ]
    )
    return branches[0].pk


def test_totals_use_one_query(django_assert_num_queries: Any) -> None:
    bulk()
    with django_assert_num_queries(1):
        totals = topic_repository.topic_totals(None, None)
    assert totals.review_count == 500


def test_overview_with_filters_uses_one_query(django_assert_num_queries: Any) -> None:
    branch_id = bulk()
    with django_assert_num_queries(1):
        topic_service.topic_overview(branch_id, 30, timezone.now())


def test_location_topics_use_one_query(django_assert_num_queries: Any) -> None:
    branch_id = bulk()
    with django_assert_num_queries(1):
        topic_service.location_topics(branch_id)


def test_month_totals_use_one_query(django_assert_num_queries: Any) -> None:
    bulk()
    now = timezone.now()
    with django_assert_num_queries(1):
        topic_service.month_topics(
            now - timedelta(days=30), now + timedelta(days=1), now - timedelta(days=60)
        )

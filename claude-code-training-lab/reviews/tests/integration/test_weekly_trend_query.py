from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review
from reviews.trend_service import weekly_trend

VN = ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime(2026, 10, 28, 12, 0, tzinfo=VN)


@pytest.mark.django_db
@pytest.mark.parametrize("review_count", [5, 200])
def test_weekly_trend_uses_one_query(
    review_count: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")
    Review.objects.bulk_create(
        Review(
            branch=branch,
            rating=1 + index % 5,
            text="ok",
            created_at=datetime(2026, 9, 8 + index % 50, 10, 0, tzinfo=VN)
            if index % 50 < 22
            else datetime(2026, 10, 1 + index % 25, 10, 0, tzinfo=VN),
        )
        for index in range(review_count)
    )

    with django_assert_num_queries(1):
        points = weekly_trend(branch.id, NOW)

    assert len(points) == 8
    assert sum(p.review_count for p in points) == review_count

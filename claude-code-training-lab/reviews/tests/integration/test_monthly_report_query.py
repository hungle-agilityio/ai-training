from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review
from reviews.report_service import monthly_report

VN = ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=VN)


@pytest.mark.django_db
@pytest.mark.parametrize(("branch_count", "review_count"), [(3, 5), (30, 500)])
def test_monthly_report_uses_one_query(
    branch_count: int, review_count: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="Demo")
    branches = [
        Branch.objects.create(business=business, name=f"Branch {i:02d}")
        for i in range(branch_count)
    ]
    Review.objects.bulk_create(
        Review(
            branch=branches[index % branch_count],
            rating=1 + index % 5,
            text="ok",
            created_at=datetime(2026, 11, 1 + index % 4, 10, 0, tzinfo=VN),
        )
        for index in range(review_count)
    )

    with django_assert_num_queries(2):
        report = monthly_report(None, NOW)

    assert len(report.rows) == branch_count
    assert sum(row.review_count for row in report.rows) == review_count

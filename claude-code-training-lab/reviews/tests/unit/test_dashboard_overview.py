from datetime import UTC, datetime, timedelta

import pytest

from reviews.models import Branch, Business, Review
from reviews.services import branch_status, dashboard_overview, review_sentiment


@pytest.mark.parametrize(
    ("average", "status"),
    [(5, "excellent"), (4, "excellent"), (3.9, "watch"), (3, "watch"), (2.9, "attention")],
)
def test_branch_status_thresholds(average: float, status: str) -> None:
    assert branch_status(average)[0] == status


@pytest.mark.parametrize(
    ("rating", "sentiment"),
    [(5, "positive"), (4, "positive"), (3, "neutral"), (2, "negative"), (1, "negative")],
)
def test_review_sentiment_thresholds(rating: int, sentiment: str) -> None:
    assert review_sentiment(rating)[0] == sentiment


@pytest.mark.django_db
def test_overview_without_data_is_empty() -> None:
    overview = dashboard_overview()

    assert overview.branch_count == 0
    assert overview.review_count == 0
    assert overview.overall_average is None
    assert [bar.count for bar in overview.rating_bars] == [0, 0, 0, 0, 0]
    assert overview.recent_reviews == []


@pytest.mark.django_db
def test_overview_summarises_branches_and_reviews() -> None:
    business = Business.objects.create(name="Demo")
    good = Branch.objects.create(business=business, name="Downtown")
    bad = Branch.objects.create(business=business, name="Airport")
    now = datetime(2026, 10, 14, tzinfo=UTC)
    for offset, (branch, rating) in enumerate([(good, 5), (good, 4), (bad, 2), (bad, 1)]):
        Review.objects.create(
            branch=branch, rating=rating, text=f"r{rating}", created_at=now - timedelta(days=offset)
        )

    overview = dashboard_overview(recent_limit=2)

    assert overview.branch_count == 2
    assert overview.review_count == 4
    assert overview.overall_average == 3.0
    assert overview.attention_count == 1
    assert {row.name: row.status for row in overview.branches} == {
        "Downtown": "excellent",
        "Airport": "attention",
    }
    assert [(bar.stars, bar.count, bar.percent) for bar in overview.rating_bars] == [
        (5, 1, 25),
        (4, 1, 25),
        (3, 0, 0),
        (2, 1, 25),
        (1, 1, 25),
    ]
    assert [review.text for review in overview.recent_reviews] == ["r5", "r4"]
    assert overview.recent_reviews[0].branch_name == "Downtown"
    assert overview.recent_reviews[0].sentiment == "positive"


def _branch_with_ratings(business: Business, name: str, ratings: list[int]) -> None:
    branch = Branch.objects.create(business=business, name=name)
    now = datetime(2026, 10, 14, tzinfo=UTC)
    Review.objects.bulk_create(
        Review(branch=branch, rating=rating, text="ok", created_at=now) for rating in ratings
    )


@pytest.mark.django_db
def test_overview_bar_follows_the_exact_average() -> None:
    # BUG-001: Riverside (4, 5, 2) is 3.7, so its bar is 74%, not 60%
    business = Business.objects.create(name="Demo")
    _branch_with_ratings(business, "Riverside", [4, 5, 2])

    row = dashboard_overview().branches[0]

    assert row.average_rating == 3.7
    assert row.bar_percent == 74


@pytest.mark.django_db
def test_overview_status_follows_the_rounded_score() -> None:
    # 74 / 25 = 2.96 shows as 3.0, so it must not be labelled "Needs attention"
    business = Business.objects.create(name="Demo")
    _branch_with_ratings(business, "Edge", [3] * 24 + [2])

    overview = dashboard_overview()

    assert overview.branches[0].average_rating == 3.0
    assert overview.branches[0].status == "watch"
    assert overview.attention_count == 0

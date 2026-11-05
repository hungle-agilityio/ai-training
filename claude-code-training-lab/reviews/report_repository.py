from dataclasses import dataclass
from datetime import datetime

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from reviews.models import Branch


@dataclass(frozen=True)
class MonthTotals:
    branch_id: int
    name: str
    review_count: int
    rating_total: int
    good_count: int
    bad_count: int


def month_totals(
    start: datetime,
    end: datetime,
    good: tuple[int, int],
    bad: tuple[int, int],
) -> list[MonthTotals]:
    """Totals of every branch for reviews from start up to end, in one query, by name then id."""
    in_month = Q(reviews__created_at__gte=start, reviews__created_at__lt=end)
    rows = (
        Branch.objects.order_by("name", "id")
        .values("id", "name")
        .annotate(
            review_count=Count("reviews", filter=in_month),
            rating_total=Coalesce(Sum("reviews__rating", filter=in_month), 0),
            good_count=Count(
                "reviews",
                filter=in_month & Q(reviews__rating__gte=good[0], reviews__rating__lte=good[1]),
            ),
            bad_count=Count(
                "reviews",
                filter=in_month & Q(reviews__rating__gte=bad[0], reviews__rating__lte=bad[1]),
            ),
        )
    )
    return [
        MonthTotals(
            branch_id=int(row["id"]),
            name=str(row["name"]),
            review_count=int(row["review_count"]),
            rating_total=int(row["rating_total"]),
            good_count=int(row["good_count"]),
            bad_count=int(row["bad_count"]),
        )
        for row in rows
    ]


@dataclass(frozen=True)
class MonthPairTotals:
    current: MonthTotals
    previous_review_count: int
    previous_rating_total: int


def month_pair_totals(
    start: datetime,
    end: datetime,
    previous_start: datetime,
    good: tuple[int, int],
    bad: tuple[int, int],
) -> list[MonthPairTotals]:
    """Totals of every branch for a month and for the month before it, in one query."""
    in_month = Q(reviews__created_at__gte=start, reviews__created_at__lt=end)
    in_previous = Q(reviews__created_at__gte=previous_start, reviews__created_at__lt=start)
    rows = (
        Branch.objects.order_by("name", "id")
        .values("id", "name")
        .annotate(
            review_count=Count("reviews", filter=in_month),
            rating_total=Coalesce(Sum("reviews__rating", filter=in_month), 0),
            good_count=Count(
                "reviews",
                filter=in_month & Q(reviews__rating__gte=good[0], reviews__rating__lte=good[1]),
            ),
            bad_count=Count(
                "reviews",
                filter=in_month & Q(reviews__rating__gte=bad[0], reviews__rating__lte=bad[1]),
            ),
            previous_count=Count("reviews", filter=in_previous),
            previous_total=Coalesce(Sum("reviews__rating", filter=in_previous), 0),
        )
    )
    return [
        MonthPairTotals(
            current=MonthTotals(
                branch_id=int(row["id"]),
                name=str(row["name"]),
                review_count=int(row["review_count"]),
                rating_total=int(row["rating_total"]),
                good_count=int(row["good_count"]),
                bad_count=int(row["bad_count"]),
            ),
            previous_review_count=int(row["previous_count"]),
            previous_rating_total=int(row["previous_total"]),
        )
        for row in rows
    ]

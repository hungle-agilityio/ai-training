from collections.abc import Sequence
from dataclasses import dataclass

from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import Coalesce

from reviews.models import Branch, Review


@dataclass(frozen=True)
class BranchTotals:
    branch_id: int
    name: str
    review_count: int
    rating_total: int


def branch_rating_totals() -> list[BranchTotals]:
    """Review count and rating sum of every branch in one query, ordered by id.

    Keep it to a single join: a second join would multiply both numbers.
    """
    rows = (
        Branch.objects.order_by("id")
        .values("id", "name")
        .annotate(review_count=Count("reviews"), rating_total=Coalesce(Sum("reviews__rating"), 0))
    )
    return [
        BranchTotals(
            branch_id=int(row["id"]),
            name=str(row["name"]),
            review_count=int(row["review_count"]),
            rating_total=int(row["rating_total"]),
        )
        for row in rows
    ]


def rating_counts() -> dict[int, int]:
    rows = Review.objects.values("rating").annotate(total=Count("id"))
    return {row["rating"]: row["total"] for row in rows}


def list_recent_reviews(limit: int) -> Sequence[Review]:
    return list(Review.objects.select_related("branch").order_by("-created_at")[:limit])


def reviews_newest_first() -> QuerySet[Review]:
    return Review.objects.select_related("branch").order_by("-created_at", "-id")

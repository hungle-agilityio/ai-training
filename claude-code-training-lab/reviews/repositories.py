from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from django.db.models import Count, Q, QuerySet, Sum
from django.db.models.functions import Coalesce

from reviews.models import Branch, Review
from reviews.search_text import normalize_for_search


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


@dataclass(frozen=True)
class RatingCounts:
    by_rating: dict[int, int]
    unreplied: int


def rating_counts() -> RatingCounts:
    """Reviews per rating and the reviews with no reply, in one query."""
    rows = Review.objects.values("rating").annotate(
        total=Count("id"), unreplied=Count("id", filter=Q(reply__isnull=True))
    )
    return RatingCounts(
        by_rating={int(row["rating"]): int(row["total"]) for row in rows},
        unreplied=sum(int(row["unreplied"]) for row in rows),
    )


def list_recent_reviews(limit: int) -> Sequence[Review]:
    return list(Review.objects.select_related("branch", "reply").order_by("-created_at")[:limit])


def branch_rating_totals_for(pk: int) -> BranchTotals | None:
    """Count and rating sum of one branch in one query; None when it does not exist."""
    row = (
        Branch.objects.filter(pk=pk)
        .values("id", "name")
        .annotate(review_count=Count("reviews"), rating_total=Coalesce(Sum("reviews__rating"), 0))
        .first()
    )
    if row is None:
        return None
    return BranchTotals(
        branch_id=int(row["id"]),
        name=str(row["name"]),
        review_count=int(row["review_count"]),
        rating_total=int(row["rating_total"]),
    )


def rating_counts_for(branch_id: int) -> dict[int, int]:
    rows = Review.objects.filter(branch_id=branch_id).values("rating").annotate(total=Count("id"))
    return {row["rating"]: row["total"] for row in rows}


def newest_reviews_of(branch_id: int, limit: int) -> Sequence[Review]:
    return list(reviews_newest_first(branch_id=branch_id)[:limit])


def reviews_newest_first(
    *,
    branch_id: int | None = None,
    ratings: tuple[int, int] | None = None,
    created_range: tuple[datetime, datetime] | None = None,
    words: Sequence[str] = (),
    replied: bool | None = None,
) -> QuerySet[Review]:
    """Newest first. `ratings` is (lowest, highest) stars; `created_range` is [start, end).

    Every normalised word in `words` must be part of the stored search text.
    `replied` True keeps reviews with a reply, False those without, None all.
    """
    reviews = Review.objects.select_related("branch", "reply").order_by("-created_at", "-id")
    if replied is not None:
        reviews = reviews.filter(reply__isnull=not replied)
    if branch_id is not None:
        reviews = reviews.filter(branch_id=branch_id)
    if ratings is not None:
        reviews = reviews.filter(rating__range=ratings)
    if created_range is not None:
        reviews = reviews.filter(created_at__gte=created_range[0], created_at__lt=created_range[1])
    for word in words:
        reviews = reviews.filter(search_text__contains=word)
    return reviews


def create_review(*, branch: Branch, rating: int, text: str, created_at: datetime) -> Review:
    """The only way to add a review, so the search copy of the text is always filled."""
    return Review.objects.create(
        branch=branch,
        rating=rating,
        text=text,
        search_text=normalize_for_search(text),
        created_at=created_at,
    )


def branch_name(pk: int) -> str | None:
    return Branch.objects.filter(pk=pk).values_list("name", flat=True).first()


def branch_choices() -> list[tuple[int, str]]:
    return [
        (pk, name) for pk, name in Branch.objects.order_by("name", "id").values_list("id", "name")
    ]

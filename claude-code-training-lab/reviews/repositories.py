from collections.abc import Sequence

from django.db.models import Count

from reviews.models import Branch, Review


def list_branches() -> Sequence[Branch]:
    return list(Branch.objects.order_by("id"))


def list_reviews_for_branch(branch_id: int) -> Sequence[Review]:
    return list(Review.objects.filter(branch_id=branch_id).order_by("created_at"))


def rating_counts() -> dict[int, int]:
    rows = Review.objects.values("rating").annotate(total=Count("id"))
    return {row["rating"]: row["total"] for row in rows}


def list_recent_reviews(limit: int) -> Sequence[Review]:
    return list(Review.objects.select_related("branch").order_by("-created_at")[:limit])

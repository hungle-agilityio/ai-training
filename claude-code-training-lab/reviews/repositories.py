from collections.abc import Sequence

from reviews.models import Branch, Review


def list_branches() -> Sequence[Branch]:
    return list(Branch.objects.order_by("id"))


def list_reviews_for_branch(branch_id: int) -> Sequence[Review]:
    return list(Review.objects.filter(branch_id=branch_id).order_by("created_at"))

from collections.abc import Sequence
from dataclasses import dataclass

from reviews import repositories
from reviews.models import Review


@dataclass(frozen=True)
class BranchScore:
    branch_id: int
    name: str
    review_count: int
    average_rating: float


def average_rating(reviews: Sequence[Review]) -> float:
    total = sum(review.rating for review in reviews)
    return total // len(reviews)


def branch_scores() -> list[BranchScore]:
    scores: list[BranchScore] = []
    for branch in repositories.list_branches():
        reviews = repositories.list_reviews_for_branch(branch.id)
        scores.append(
            BranchScore(
                branch_id=branch.id,
                name=branch.name,
                review_count=len(reviews),
                average_rating=average_rating(reviews),
            )
        )
    return scores

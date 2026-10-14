from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

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


@dataclass(frozen=True)
class BranchRow:
    name: str
    review_count: int
    average_rating: float
    bar_percent: int
    status: str
    status_label: str


@dataclass(frozen=True)
class RatingBar:
    stars: int
    count: int
    percent: int


@dataclass(frozen=True)
class RecentReview:
    branch_name: str
    rating: int
    text: str
    created_at: datetime
    sentiment: str
    sentiment_label: str


@dataclass(frozen=True)
class DashboardOverview:
    branch_count: int
    review_count: int
    overall_average: float | None
    overall_percent: int
    attention_count: int
    branches: list[BranchRow]
    rating_bars: list[RatingBar]
    recent_reviews: list[RecentReview]


def branch_status(average: float) -> tuple[str, str]:
    if average >= 4:
        return "excellent", "Excellent"
    if average >= 3:
        return "watch", "Watch"
    return "attention", "Needs attention"


def review_sentiment(rating: int) -> tuple[str, str]:
    if rating >= 4:
        return "positive", "Positive"
    if rating == 3:
        return "neutral", "Neutral"
    return "negative", "Negative"


def dashboard_overview(recent_limit: int = 6) -> DashboardOverview:
    rows = []
    for score in branch_scores():
        status, label = branch_status(score.average_rating)
        rows.append(
            BranchRow(
                name=score.name,
                review_count=score.review_count,
                average_rating=score.average_rating,
                bar_percent=round(score.average_rating / 5 * 100),
                status=status,
                status_label=label,
            )
        )

    counts = repositories.rating_counts()
    total = sum(counts.values())
    overall = sum(stars * count for stars, count in counts.items()) / total if total else None
    bars = [
        RatingBar(
            stars=stars,
            count=counts.get(stars, 0),
            percent=round(counts.get(stars, 0) / total * 100) if total else 0,
        )
        for stars in (5, 4, 3, 2, 1)
    ]

    recent = []
    for review in repositories.list_recent_reviews(recent_limit):
        sentiment, sentiment_label = review_sentiment(review.rating)
        recent.append(
            RecentReview(
                branch_name=review.branch.name,
                rating=review.rating,
                text=review.text,
                created_at=review.created_at,
                sentiment=sentiment,
                sentiment_label=sentiment_label,
            )
        )

    return DashboardOverview(
        branch_count=len(rows),
        review_count=total,
        overall_average=overall,
        overall_percent=round(overall / 5 * 100) if overall is not None else 0,
        attention_count=sum(1 for row in rows if row.status == "attention"),
        branches=rows,
        rating_bars=bars,
        recent_reviews=recent,
    )

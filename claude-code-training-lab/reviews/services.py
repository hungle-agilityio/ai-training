from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.core.paginator import Paginator

from reviews import repositories
from reviews.models import Review

REVIEWS_PER_PAGE = 20
TEXT_PREVIEW_LENGTH = 120
# A week is Monday to Sunday in Vietnam time, whatever time zone is active
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
RATING_RANGES: dict[str, tuple[int, int]] = {"good": (4, 5), "bad": (1, 2)}


@dataclass(frozen=True)
class BranchScore:
    branch_id: int
    name: str
    review_count: int
    average_rating: float


def rounded_average(total: int, count: int) -> float:
    """Average to one decimal, rounding half up (2.25 -> 2.3) like Excel and a hand calculation."""
    average = Decimal(total) / Decimal(count)
    return float(average.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def average_rating(reviews: Sequence[Review]) -> float:
    return rounded_average(sum(review.rating for review in reviews), len(reviews))


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
class ReviewRow:
    branch_name: str
    rating: int
    rating_percent: int
    text: str
    text_short: str
    is_truncated: bool
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
    recent_reviews: list[ReviewRow]


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


def shorten_text(text: str) -> tuple[str, bool]:
    if len(text) <= TEXT_PREVIEW_LENGTH:
        return text, False
    return text[:TEXT_PREVIEW_LENGTH].rstrip() + "…", True


def to_review_row(review: Review) -> ReviewRow:
    sentiment, sentiment_label = review_sentiment(review.rating)
    text_short, is_truncated = shorten_text(review.text)
    return ReviewRow(
        branch_name=review.branch.name,
        rating=review.rating,
        rating_percent=round(review.rating / 5 * 100),
        text=review.text,
        text_short=text_short,
        is_truncated=is_truncated,
        created_at=review.created_at,
        sentiment=sentiment,
        sentiment_label=sentiment_label,
    )


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

    recent = [to_review_row(review) for review in repositories.list_recent_reviews(recent_limit)]

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


@dataclass(frozen=True)
class PageLink:
    number: int | None
    is_current: bool
    href: str


@dataclass(frozen=True)
class ReviewFilters:
    branch_id: int | None = None
    rating: str | None = None
    day: date | None = None


@dataclass(frozen=True)
class WeekRange:
    start: datetime
    end: datetime
    label: str


@dataclass(frozen=True)
class BranchOption:
    id: int
    name: str
    is_selected: bool


@dataclass(frozen=True)
class ReviewsPage:
    rows: list[ReviewRow]
    number: int
    num_pages: int
    total: int
    start_index: int
    end_index: int
    has_previous: bool
    has_next: bool
    previous_number: int
    next_number: int
    links: list[PageLink]
    previous_href: str
    next_href: str
    branches: list[BranchOption]
    rating: str
    week_value: str
    week_label: str | None
    is_filtered: bool
    query_params: list[tuple[str, str]]


def week_label(monday: date) -> str:
    sunday = monday + timedelta(days=6)
    start = f"{monday:%b} {monday.day}"
    end = f"{sunday:%b} {sunday.day}, {sunday.year}"
    if monday.year != sunday.year:
        start += f", {monday.year}"
    return f"{start} - {end}"


def week_containing(day: date) -> WeekRange:
    """Monday to Sunday of `day`, as the half-open range [Monday 00:00, next Monday 00:00)."""
    monday = day - timedelta(days=day.weekday())
    return WeekRange(
        start=datetime.combine(monday, time.min, tzinfo=VIETNAM_TZ),
        end=datetime.combine(monday + timedelta(days=7), time.min, tzinfo=VIETNAM_TZ),
        label=week_label(monday),
    )


def page_href(params: list[tuple[str, str]], number: int) -> str:
    return "?" + urlencode([*params, ("page", str(number))])


def reviews_page(
    page: int | None,
    per_page: int = REVIEWS_PER_PAGE,
    filters: ReviewFilters | None = None,
) -> ReviewsPage:
    filters = filters or ReviewFilters()
    choices = repositories.branch_choices()
    branch_id = filters.branch_id if filters.branch_id in {pk for pk, _ in choices} else None
    ratings = RATING_RANGES.get(filters.rating or "")
    week = week_containing(filters.day) if filters.day else None

    params: list[tuple[str, str]] = []
    if branch_id is not None:
        params.append(("location", str(branch_id)))
    if ratings is not None and filters.rating:
        params.append(("rating", filters.rating))
    if filters.day is not None:
        params.append(("week", filters.day.isoformat()))

    reviews = repositories.reviews_newest_first(
        branch_id=branch_id,
        ratings=ratings,
        created_range=(week.start, week.end) if week else None,
    )
    paginator = Paginator(reviews, per_page)
    current = paginator.get_page(page or 1)
    rows = [to_review_row(review) for review in current.object_list]

    links = [
        PageLink(
            number=item if isinstance(item, int) else None,
            is_current=item == current.number,
            href=page_href(params, item) if isinstance(item, int) else "",
        )
        for item in paginator.get_elided_page_range(current.number, on_each_side=1, on_ends=1)
    ]
    previous_number = max(current.number - 1, 1)
    next_number = min(current.number + 1, paginator.num_pages)

    return ReviewsPage(
        rows=rows,
        number=current.number,
        num_pages=paginator.num_pages,
        total=paginator.count,
        start_index=current.start_index(),
        end_index=current.end_index(),
        has_previous=current.has_previous(),
        has_next=current.has_next(),
        previous_number=previous_number,
        next_number=next_number,
        links=links,
        previous_href=page_href(params, previous_number),
        next_href=page_href(params, next_number),
        branches=[BranchOption(pk, name, pk == branch_id) for pk, name in choices],
        rating=filters.rating if ratings is not None and filters.rating else "",
        week_value=filters.day.isoformat() if filters.day else "",
        week_label=week.label if week else None,
        is_filtered=bool(params),
        query_params=params,
    )

import csv
import io
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.core.paginator import Paginator
from django.db.models import QuerySet

from reviews import repositories
from reviews.models import Review
from reviews.search_text import normalize_for_search, tidy_search_input

REVIEWS_PER_PAGE = 20
TEXT_PREVIEW_LENGTH = 120
# A week is Monday to Sunday in Vietnam time, whatever time zone is active
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
# Choices of the Rating filter: the good / bad bands, then one exact star count each.
RATING_RANGES: dict[str, tuple[int, int]] = {
    "good": (4, 5),
    "bad": (1, 2),
    **{str(stars): (stars, stars) for stars in (5, 4, 3, 2, 1)},
}
SEARCH_MIN_LENGTH = 3
CSV_CHUNK_ROWS = 500
CSV_CHUNK_BYTES = 64 * 1024
CSV_HEADER = ("Location", "Rating", "Review text", "Date")
# Excel needs the UTF-8 marker to show Vietnamese letters correctly
CSV_BOM = "\ufeff"
# A spreadsheet reads a cell starting with one of these as a formula
CSV_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


@dataclass(frozen=True)
class BranchScore:
    branch_id: int
    name: str
    review_count: int
    average_rating: float | None


def rounded_average(total: int, count: int) -> float:
    """Average to one decimal, rounding half up (2.25 -> 2.3) like Excel and a hand calculation."""
    average = Decimal(total) / Decimal(count)
    return float(average.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def average_from_totals(total: int, count: int) -> float | None:
    """The one rule for a location's score: None when it has no reviews yet."""
    if count == 0:
        return None
    return rounded_average(total, count)


def average_rating(reviews: Sequence[Review]) -> float | None:
    return average_from_totals(sum(review.rating for review in reviews), len(reviews))


def branch_scores() -> list[BranchScore]:
    return [
        BranchScore(
            branch_id=totals.branch_id,
            name=totals.name,
            review_count=totals.review_count,
            average_rating=average_from_totals(totals.rating_total, totals.review_count),
        )
        for totals in repositories.branch_rating_totals()
    ]


@dataclass(frozen=True)
class BranchRow:
    branch_id: int
    name: str
    review_count: int
    average_rating: float | None
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
        if score.average_rating is None:
            # No reviews yet: no score, no bar, no status, and not "needs attention"
            rows.append(
                BranchRow(
                    branch_id=score.branch_id,
                    name=score.name,
                    review_count=score.review_count,
                    average_rating=None,
                    bar_percent=0,
                    status="",
                    status_label="",
                )
            )
            continue
        status, label = branch_status(score.average_rating)
        rows.append(
            BranchRow(
                branch_id=score.branch_id,
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
    search: str = ""


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
    branch_id: int | None
    rating: str
    week_value: str
    week_label: str | None
    search_value: str
    search_too_short: bool
    show_clear: bool
    is_filtered: bool
    query_params: list[tuple[str, str]]
    export_query: str


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


@dataclass(frozen=True)
class ReviewSelection:
    """The filters that really apply, after a wrong value has been ignored."""

    branch_id: int | None
    rating: str | None
    week: WeekRange | None
    day: date | None
    params: list[tuple[str, str]]
    search: str
    search_words: tuple[str, ...]
    search_too_short: bool


def search_words(term: str) -> tuple[str, ...]:
    """Words that must all appear in a review; empty when shorter than SEARCH_MIN_LENGTH."""
    tidy = tidy_search_input(term)
    if len(tidy) < SEARCH_MIN_LENGTH:
        return ()
    return tuple(dict.fromkeys(normalize_for_search(tidy).split()))


def resolve_selection(filters: ReviewFilters, branch_ids: set[int]) -> ReviewSelection:
    branch_id = filters.branch_id if filters.branch_id in branch_ids else None
    rating = filters.rating if filters.rating in RATING_RANGES else None
    week = week_containing(filters.day) if filters.day else None

    typed = tidy_search_input(filters.search)
    search_too_short = 0 < len(typed) < SEARCH_MIN_LENGTH
    search = "" if search_too_short else typed

    params: list[tuple[str, str]] = []
    if search:
        params.append(("search", search))
    if branch_id is not None:
        params.append(("location", str(branch_id)))
    if rating is not None:
        params.append(("rating", rating))
    if filters.day is not None:
        params.append(("week", filters.day.isoformat()))
    return ReviewSelection(
        branch_id, rating, week, filters.day, params, search, search_words(search), search_too_short
    )


def matching_reviews(selection: ReviewSelection) -> QuerySet[Review]:
    return repositories.reviews_newest_first(
        branch_id=selection.branch_id,
        ratings=RATING_RANGES[selection.rating] if selection.rating else None,
        created_range=(selection.week.start, selection.week.end) if selection.week else None,
        words=selection.search_words,
    )


def csv_safe(value: str) -> str:
    """Prefix a single quote so a spreadsheet shows the text as plain text, never a formula."""
    return "'" + value if value.startswith(CSV_FORMULA_STARTS) else value


def export_filename(now: datetime) -> str:
    return f"reviews-{now.astimezone(VIETNAM_TZ):%Y-%m-%d}.csv"


def reviews_csv(filters: ReviewFilters) -> Iterator[str]:
    """The CSV of every matching review in chunks, so a long list never sits in memory at once."""
    selection = resolve_selection(filters, {pk for pk, _ in repositories.branch_choices()})
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")

    def flush() -> str:
        chunk = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate()
        return chunk

    writer.writerow(CSV_HEADER)
    yield CSV_BOM + flush()
    for review in matching_reviews(selection).iterator(chunk_size=CSV_CHUNK_ROWS):
        writer.writerow(
            (
                csv_safe(review.branch.name),
                review.rating,
                csv_safe(review.text),
                f"{review.created_at.astimezone(VIETNAM_TZ):%Y-%m-%d %H:%M}",
            )
        )
        if buffer.tell() >= CSV_CHUNK_BYTES:
            yield flush()
    yield flush()


def reviews_page(
    page: int | None,
    per_page: int = REVIEWS_PER_PAGE,
    filters: ReviewFilters | None = None,
) -> ReviewsPage:
    filters = filters or ReviewFilters()
    choices = repositories.branch_choices()
    selection = resolve_selection(filters, {pk for pk, _ in choices})
    branch_id, week, params = selection.branch_id, selection.week, selection.params
    search_value = tidy_search_input(filters.search)
    reviews = matching_reviews(selection)
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
        branch_id=branch_id,
        rating=selection.rating or "",
        week_value=selection.day.isoformat() if selection.day else "",
        week_label=week.label if week else None,
        search_value=search_value,
        search_too_short=selection.search_too_short,
        show_clear=bool(params) or bool(search_value),
        is_filtered=bool(params),
        query_params=params,
        export_query=urlencode(params),
    )

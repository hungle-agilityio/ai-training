import csv
import io
import re
import unicodedata
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.utils import timezone

from reviews import repositories
from reviews.goals import GoalStatus, goal_status
from reviews.models import Review
from reviews.search_text import normalize_for_search, tidy_search_input
from reviews.topics import TOPICS, topic_by_slug

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
# Choices of the Reply filter: `yes` keeps reviews with a reply, `no` those without.
REPLY_CHOICES: dict[str, bool] = {"yes": True, "no": False}
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
    reply_percent: int | None = None
    goal: GoalStatus | None = None


@dataclass(frozen=True)
class ReplySpeed:
    counted: int = 0
    replied: int = 0
    replied_in_time: int = 0
    percent: int | None = None
    average_hours: float | None = None
    average_label: str = ""


SECONDS_PER_HOUR = Decimal(3600)
DAYS_FROM_HOURS = Decimal(48)


def reply_share_percent(replied_in_time: int, counted: int) -> int | None:
    """Whole percent of counted bad reviews replied in 24 hours, half up; None when none counted."""
    if counted == 0:
        return None
    share = Decimal(replied_in_time) * 100 / Decimal(counted)
    return int(share.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _mean_hours(total_seconds: float, count: int) -> Decimal:
    return Decimal(total_seconds) / SECONDS_PER_HOUR / Decimal(count)


def average_reply_hours(total_seconds: float, count: int) -> float | None:
    """Mean reply time in hours to one decimal, half up; None when no review has a reply."""
    if count == 0:
        return None
    return float(_mean_hours(total_seconds, count).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def reply_time_label(total_seconds: float, count: int) -> str:
    """Hours under 48, days from 48; the choice uses the unrounded mean."""
    if count == 0:
        return ""
    hours = _mean_hours(total_seconds, count)
    if hours < DAYS_FROM_HOURS:
        return f"{hours.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)} h"
    days = (hours / 24).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{days} days"


def overdue_total(rows: Sequence[repositories.BranchTotals]) -> int:
    """Bad reviews past 24 hours with no reply: the counted ones minus those with a reply."""
    return sum(row.bad_counted - row.bad_replied for row in rows)


def _reply_speed(counted: int, replied: int, in_time: int, seconds: float) -> ReplySpeed:
    return ReplySpeed(
        counted=counted,
        replied=replied,
        replied_in_time=in_time,
        percent=reply_share_percent(in_time, counted),
        average_hours=average_reply_hours(seconds, replied),
        average_label=reply_time_label(seconds, replied),
    )


def reply_speed_of(totals: repositories.BranchTotals) -> ReplySpeed:
    return _reply_speed(
        totals.bad_counted,
        totals.bad_replied,
        totals.bad_replied_in_time,
        totals.reply_seconds,
    )


def total_reply_speed(rows: Sequence[repositories.BranchTotals]) -> ReplySpeed:
    return _reply_speed(
        sum(row.bad_counted for row in rows),
        sum(row.bad_replied for row in rows),
        sum(row.bad_replied_in_time for row in rows),
        sum(row.reply_seconds for row in rows),
    )


@dataclass(frozen=True)
class RatingBar:
    stars: int
    count: int
    percent: int


@dataclass(frozen=True)
class ReviewRow:
    review_id: int
    has_reply: bool
    branch_id: int
    branch_name: str
    rating: int
    rating_percent: int
    text: str
    text_short: str
    is_truncated: bool
    created_at: datetime
    sentiment: str
    sentiment_label: str
    # Follow-up status and its label; empty when the row shows no follow-up badge
    followup: str = ""
    followup_label: str = ""


@dataclass(frozen=True)
class DashboardOverview:
    branch_count: int
    review_count: int
    overall_average: float | None
    overall_percent: int
    attention_count: int
    needs_reply_count: int
    branches: list[BranchRow]
    rating_bars: list[RatingBar]
    recent_reviews: list[ReviewRow]
    reply_speed: ReplySpeed = ReplySpeed()
    overdue_count: int = 0


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


def followup_of(review: Review) -> tuple[str, str]:
    """Status and label of a bad review's case; a review that is not bad has neither."""
    from reviews import followup  # late: it imports this module

    if not followup.has_case(review.rating):
        return "", ""
    status = followup.status_of(review.followup.status if hasattr(review, "followup") else None)
    return status, followup.STATUS_LABELS[status]


def to_review_row(review: Review, *, with_followup: bool = False) -> ReviewRow:
    """`with_followup` only for reviews read together with their follow-up case."""
    sentiment, sentiment_label = review_sentiment(review.rating)
    followup, followup_label = followup_of(review) if with_followup else ("", "")
    text_short, is_truncated = shorten_text(review.text)
    return ReviewRow(
        review_id=review.id,
        has_reply=hasattr(review, "reply"),
        branch_id=review.branch_id,
        branch_name=review.branch.name,
        rating=review.rating,
        rating_percent=round(review.rating / 5 * 100),
        text=review.text,
        text_short=text_short,
        is_truncated=is_truncated,
        created_at=review.created_at,
        sentiment=sentiment,
        sentiment_label=sentiment_label,
        followup=followup,
        followup_label=followup_label,
    )


LOCATION_PAGE_REVIEWS = 5


@dataclass(frozen=True)
class LocationPage:
    branch_id: int
    name: str
    review_count: int
    average_rating: float | None
    bar_percent: int
    status: str
    status_label: str
    rating_bars: list[RatingBar]
    latest_reviews: list[ReviewRow]
    goal: GoalStatus


def rating_bars_from(counts: dict[int, int]) -> list[RatingBar]:
    total = sum(counts.values())
    return [
        RatingBar(
            stars=stars,
            count=counts.get(stars, 0),
            percent=round(counts.get(stars, 0) / total * 100) if total else 0,
        )
        for stars in (5, 4, 3, 2, 1)
    ]


def location_page(pk: int) -> LocationPage | None:
    """Score, breakdown and newest reviews of one location; None when it does not exist."""
    totals = repositories.branch_rating_totals_for(pk)
    if totals is None:
        return None
    average = average_from_totals(totals.rating_total, totals.review_count)
    status, status_label = ("", "") if average is None else branch_status(average)
    has_reviews = totals.review_count > 0
    newest = repositories.newest_reviews_of(pk, LOCATION_PAGE_REVIEWS) if has_reviews else []
    return LocationPage(
        branch_id=totals.branch_id,
        name=totals.name,
        review_count=totals.review_count,
        average_rating=average,
        bar_percent=round(average / 5 * 100) if average is not None else 0,
        status=status,
        status_label=status_label,
        rating_bars=rating_bars_from(repositories.rating_counts_for(pk)),
        latest_reviews=[to_review_row(review) for review in newest],
        goal=goal_status(average, totals.target_score),
    )


def dashboard_overview(recent_limit: int = 6, now: datetime | None = None) -> DashboardOverview:
    rows = []
    totals_list = repositories.branch_rating_totals(now=now or timezone.now())
    for totals in totals_list:
        score = BranchScore(
            branch_id=totals.branch_id,
            name=totals.name,
            review_count=totals.review_count,
            average_rating=average_from_totals(totals.rating_total, totals.review_count),
        )
        reply_percent = reply_speed_of(totals).percent
        goal = goal_status(score.average_rating, totals.target_score)
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
                    reply_percent=reply_percent,
                    goal=goal,
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
                reply_percent=reply_percent,
                goal=goal,
            )
        )

    rating_totals = repositories.rating_counts()
    counts = rating_totals.by_rating
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
        needs_reply_count=rating_totals.unreplied,
        branches=rows,
        rating_bars=bars,
        recent_reviews=recent,
        reply_speed=total_reply_speed(totals_list),
        overdue_count=overdue_total(totals_list),
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
    reply: str | None = None
    topic: str | None = None
    followup: str | None = None


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
    reply: str
    topic: str
    week_value: str
    week_label: str | None
    search_value: str
    search_too_short: bool
    show_clear: bool
    is_filtered: bool
    query_params: list[tuple[str, str]]
    export_query: str
    topic_options: tuple[tuple[str, str], ...] = ()
    followup: str = ""
    followup_options: tuple[tuple[str, str], ...] = ()


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
    reply: str | None
    topic: str | None = None
    followup: str | None = None


def search_words(term: str) -> tuple[str, ...]:
    """Words that must all appear in a review; empty when shorter than SEARCH_MIN_LENGTH."""
    tidy = tidy_search_input(term)
    if len(tidy) < SEARCH_MIN_LENGTH:
        return ()
    return tuple(dict.fromkeys(normalize_for_search(tidy).split()))


def resolve_selection(filters: ReviewFilters, branch_ids: set[int]) -> ReviewSelection:
    from reviews.followup import STATUS_LABELS  # late: it imports this module

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
    reply = filters.reply if filters.reply in REPLY_CHOICES else None
    if reply is not None:
        params.append(("reply", reply))
    topic = filters.topic if topic_by_slug(filters.topic or "") else None
    if topic is not None:
        params.append(("topic", topic))
    followup = filters.followup if filters.followup in STATUS_LABELS else None
    if followup is not None:
        params.append(("followup", followup))
    return ReviewSelection(
        branch_id,
        rating,
        week,
        filters.day,
        params,
        search,
        search_words(search),
        search_too_short,
        reply,
        topic,
        followup,
    )


def matching_reviews(selection: ReviewSelection) -> QuerySet[Review]:
    return repositories.reviews_newest_first(
        branch_id=selection.branch_id,
        ratings=RATING_RANGES[selection.rating] if selection.rating else None,
        created_range=(selection.week.start, selection.week.end) if selection.week else None,
        words=selection.search_words,
        replied=REPLY_CHOICES[selection.reply] if selection.reply else None,
        topic=topic_by_slug(selection.topic or ""),
        followup=selection.followup,
    )


def csv_safe(value: str) -> str:
    """Prefix a single quote so a spreadsheet shows the text as plain text, never a formula."""
    return "'" + value if value.startswith(CSV_FORMULA_STARTS) else value


def location_slug(name: str, pk: int) -> str:
    """Lower case ASCII words joined by one dash; `location-<id>` when nothing is left."""
    plain = unicodedata.normalize("NFD", name.replace("đ", "d").replace("Đ", "D"))
    ascii_name = "".join(ch for ch in plain if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-") or f"location-{pk}"


def export_filename(now: datetime, location: str | None = None) -> str:
    day = f"{now.astimezone(VIETNAM_TZ):%Y-%m-%d}"
    return f"reviews-{location}-{day}.csv" if location else f"reviews-{day}.csv"


def export_filename_for(filters: ReviewFilters, now: datetime) -> str:
    """The export name carries the filtered location; a missing or unknown one is left out."""
    if filters.branch_id is None:
        return export_filename(now)
    name = repositories.branch_name(filters.branch_id)
    if name is None:
        return export_filename(now)
    return export_filename(now, location_slug(name, filters.branch_id))


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
    from reviews.followup import STATUS_LABELS  # late: it imports this module

    filters = filters or ReviewFilters()
    choices = repositories.branch_choices()
    selection = resolve_selection(filters, {pk for pk, _ in choices})
    branch_id, week, params = selection.branch_id, selection.week, selection.params
    search_value = tidy_search_input(filters.search)
    reviews = matching_reviews(selection)
    paginator = Paginator(reviews, per_page)
    current = paginator.get_page(page or 1)
    rows = [to_review_row(review, with_followup=True) for review in current.object_list]

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
        reply=selection.reply or "",
        topic=selection.topic or "",
        week_value=selection.day.isoformat() if selection.day else "",
        week_label=week.label if week else None,
        search_value=search_value,
        search_too_short=selection.search_too_short,
        show_clear=bool(params) or bool(search_value),
        is_filtered=bool(params),
        query_params=params,
        export_query=urlencode(params),
        topic_options=tuple((topic.slug, topic.label) for topic in TOPICS),
        followup=selection.followup or "",
        followup_options=tuple(STATUS_LABELS.items()),
    )

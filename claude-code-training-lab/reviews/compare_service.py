import csv
import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from reviews import compare_repository, topic_repository
from reviews.compare_repository import STARS, CompareTotals
from reviews.services import (
    CSV_BOM,
    RATING_RANGES,
    average_from_totals,
    csv_safe,
    location_slug,
    reply_share_percent,
)
from reviews.topic_service import percent
from reviews.topics import TOPICS

PERIOD_LABELS: dict[int | None, str] = {None: "All time", 30: "Last 30 days", 90: "Last 90 days"}


@dataclass(frozen=True)
class StarRow:
    stars: int
    count: int
    percent: int


@dataclass(frozen=True)
class LocationSide:
    branch_id: int
    name: str
    review_count: int
    average_rating: float | None
    good_percent: int | None
    bad_percent: int | None
    replied_in_time_percent: int | None
    star_rows: tuple[StarRow, ...]


@dataclass(frozen=True)
class TopicCount:
    review_count: int
    bad_count: int


@dataclass(frozen=True)
class TopicRow:
    label: str
    a: TopicCount
    b: TopicCount


@dataclass(frozen=True)
class Comparison:
    period_days: int | None
    period_label: str
    a: LocationSide
    b: LocationSide
    difference: float | None
    topic_rows: tuple[TopicRow, ...]


def _share(count: int, whole: int) -> int | None:
    return percent(count, whole) if whole else None


def _side(totals: CompareTotals) -> LocationSide:
    count = totals.review_count
    by_star = dict(zip(STARS, totals.star_counts, strict=True))
    good_low, good_high = RATING_RANGES["good"]
    bad_low, bad_high = RATING_RANGES["bad"]
    good = sum(n for star, n in by_star.items() if good_low <= star <= good_high)
    bad = sum(n for star, n in by_star.items() if bad_low <= star <= bad_high)
    return LocationSide(
        branch_id=totals.branch_id,
        name=totals.name,
        review_count=count,
        average_rating=average_from_totals(totals.rating_total, count),
        good_percent=_share(good, count),
        bad_percent=_share(bad, count),
        replied_in_time_percent=reply_share_percent(totals.bad_replied_in_time, totals.bad_counted),
        star_rows=tuple(StarRow(star, n, percent(n, count)) for star, n in by_star.items()),
    )


def _difference(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    diff = Decimal(str(a)) - Decimal(str(b))
    return float(diff.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _label(period_days: int | None) -> str:
    return PERIOD_LABELS.get(period_days) or "Last " + str(period_days) + " days"


def _topic_rows(a_id: int, b_id: int, created_from: datetime | None) -> tuple[TopicRow, ...]:
    a_totals = topic_repository.topic_totals(a_id, created_from).topics
    b_totals = topic_repository.topic_totals(b_id, created_from).topics
    labels = {topic.slug: topic.label for topic in TOPICS}
    return tuple(
        TopicRow(
            labels[a.slug],
            TopicCount(a.review_count, a.bad_count),
            TopicCount(b.review_count, b.bad_count),
        )
        for a, b in zip(a_totals, b_totals, strict=True)
        if a.review_count or b.review_count
    )


def compare_locations(
    a_id: int, b_id: int, period_days: int | None, now: datetime, with_topics: bool = True
) -> Comparison | None:
    """The numbers of the Compare page; None when an id is not a location or both are the same."""
    if a_id == b_id:
        return None
    created_from = now - timedelta(days=period_days) if period_days else None
    found = compare_repository.compare_totals((a_id, b_id), created_from, now)
    rows = {t.branch_id: t for t in found}
    if a_id not in rows or b_id not in rows:
        return None
    a, b = _side(rows[a_id]), _side(rows[b_id])
    return Comparison(
        period_days=period_days,
        period_label=_label(period_days),
        a=a,
        b=b,
        difference=_difference(a.average_rating, b.average_rating),
        topic_rows=_topic_rows(a_id, b_id, created_from) if with_topics else (),
    )


PERIOD_SLUGS: dict[int | None, str] = {None: "all-time", 30: "30-days", 90: "90-days"}


def export_filename(comparison: Comparison) -> str:
    period = PERIOD_SLUGS.get(comparison.period_days) or f"{comparison.period_days}-days"
    a, b = comparison.a, comparison.b
    slug_a, slug_b = location_slug(a.name, a.branch_id), location_slug(b.name, b.branch_id)
    return f"compare-{slug_a}-{slug_b}-{period}.csv"


def _cell(value: object) -> str:
    return "" if value is None else str(value)


def comparison_csv(comparison: Comparison) -> str:
    """The Compare table as CSV text: BOM first, CRLF line ends, names safe for a spreadsheet."""
    a, b = comparison.a, comparison.b
    score = [None if s.average_rating is None else f"{s.average_rating:.1f}" for s in (a, b)]
    rows: list[tuple[str, object, object]] = [
        ("Reviews", a.review_count, b.review_count),
        ("Score", score[0], score[1]),
        ("Good reviews %", a.good_percent, b.good_percent),
        ("Bad reviews %", a.bad_percent, b.bad_percent),
        ("Replied in 24h %", a.replied_in_time_percent, b.replied_in_time_percent),
    ]
    for a_row, b_row in zip(a.star_rows, b.star_rows, strict=True):
        label = f"{a_row.stars} star" + ("" if a_row.stars == 1 else "s")
        rows.append((label, a_row.count, b_row.count))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(("Measure", csv_safe(a.name), csv_safe(b.name)))
    for label, left, right in rows:
        writer.writerow((label, _cell(left), _cell(right)))
    return CSV_BOM + buffer.getvalue()

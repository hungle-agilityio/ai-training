from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from reviews import repositories, topic_repository
from reviews.services import average_from_totals
from reviews.topics import TOPICS

LOCATION_TOPIC_LIMIT = 3
LABELS = {topic.slug: topic.label for topic in TOPICS}


@dataclass(frozen=True)
class TopicRow:
    slug: str
    label: str
    review_count: int
    share_percent: int
    bad_count: int
    bad_percent: int
    average_rating: float | None


@dataclass(frozen=True)
class TopicOverview:
    review_count: int
    no_topic_count: int
    rows: tuple[TopicRow, ...]


@dataclass(frozen=True)
class LocationTopic:
    slug: str
    label: str
    review_count: int
    bad_count: int


@dataclass(frozen=True)
class MonthTopic:
    slug: str
    label: str
    review_count: int
    bad_count: int
    change: int


def percent(part: int, whole: int) -> int:
    """A whole percent rounded half up; 0 when there is nothing to divide."""
    if whole == 0:
        return 0
    return int((Decimal(part * 100) / Decimal(whole)).quantize(Decimal("1"), ROUND_HALF_UP))


def topic_overview(branch_id: int | None, period_days: int | None, now: datetime) -> TopicOverview:
    created_from = now - timedelta(days=period_days) if period_days else None
    totals = topic_repository.topic_totals(branch_id, created_from)
    rows = [
        TopicRow(
            slug=item.slug,
            label=LABELS[item.slug],
            review_count=item.review_count,
            share_percent=percent(item.review_count, totals.review_count),
            bad_count=item.bad_count,
            bad_percent=percent(item.bad_count, item.review_count),
            average_rating=average_from_totals(item.rating_total, item.review_count),
        )
        for item in totals.topics
    ]
    rows.sort(key=lambda row: (-row.review_count, row.label))
    return TopicOverview(
        review_count=totals.review_count,
        no_topic_count=totals.no_topic_count,
        rows=tuple(rows),
    )


def location_options() -> tuple[tuple[int, str], ...]:
    return tuple(repositories.branch_choices())


def summary_line(overview: TopicOverview) -> str:
    reviews = overview.review_count
    line = f"{reviews} review" + ("" if reviews == 1 else "s")
    missing = overview.no_topic_count
    if missing:
        line += f" · {missing} " + ("mentions" if missing == 1 else "mention") + " no topic"
    return line


def location_topics(branch_id: int) -> tuple[LocationTopic, ...]:
    totals = topic_repository.topic_totals(branch_id, None)
    found = [
        LocationTopic(item.slug, LABELS[item.slug], item.review_count, item.bad_count)
        for item in totals.topics
        if item.review_count > 0
    ]
    found.sort(key=lambda topic: (-topic.review_count, topic.label))
    return tuple(found[:LOCATION_TOPIC_LIMIT])


def month_topics(
    start: datetime, end: datetime, previous_start: datetime
) -> tuple[MonthTopic, ...]:
    totals = topic_repository.month_topic_totals(start, end, previous_start)
    found = [
        MonthTopic(
            item.slug,
            LABELS[item.slug],
            item.review_count,
            item.bad_count,
            item.review_count - item.previous_count,
        )
        for item in totals
        if item.review_count > 0 or item.previous_count > 0
    ]
    found.sort(key=lambda topic: (-topic.review_count, topic.label))
    return tuple(found)

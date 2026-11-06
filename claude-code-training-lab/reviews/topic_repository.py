from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from operator import or_
from typing import Any

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from reviews.models import Review
from reviews.services import RATING_RANGES
from reviews.topics import TOPICS, Topic, normalized_keywords

BAD_LOW, BAD_HIGH = RATING_RANGES["bad"]


@dataclass(frozen=True)
class TopicTotals:
    slug: str
    review_count: int
    bad_count: int
    rating_total: int


@dataclass(frozen=True)
class TopicOverviewTotals:
    review_count: int
    no_topic_count: int
    topics: tuple[TopicTotals, ...]


@dataclass(frozen=True)
class MonthTopicTotals:
    slug: str
    review_count: int
    bad_count: int
    previous_count: int


def topic_condition(topic: Topic) -> Q:
    """A review mentions the topic: one normalised keyword is part of its search text."""
    return reduce(or_, (Q(search_text__contains=word) for word in normalized_keywords(topic)))


def _bad() -> Q:
    return Q(rating__gte=BAD_LOW, rating__lte=BAD_HIGH)


def topic_totals(branch_id: int | None, created_from: datetime | None) -> TopicOverviewTotals:
    """Totals of every topic, all reviews and reviews with no topic, in one query."""
    reviews = Review.objects.all()
    if branch_id is not None:
        reviews = reviews.filter(branch_id=branch_id)
    if created_from is not None:
        reviews = reviews.filter(created_at__gte=created_from)
    conditions = [topic_condition(topic) for topic in TOPICS]
    aggregates: dict[str, Any] = {
        "all_count": Count("id"),
        "no_topic": Count("id", filter=~reduce(or_, conditions)),
    }
    for topic, condition in zip(TOPICS, conditions, strict=True):
        aggregates[topic.slug + "_n"] = Count("id", filter=condition)
        aggregates[topic.slug + "_bad"] = Count("id", filter=condition & _bad())
        aggregates[topic.slug + "_sum"] = Coalesce(Sum("rating", filter=condition), 0)
    row = reviews.aggregate(**aggregates)
    return TopicOverviewTotals(
        review_count=int(row["all_count"]),
        no_topic_count=int(row["no_topic"]),
        topics=tuple(
            TopicTotals(
                slug=topic.slug,
                review_count=int(row[topic.slug + "_n"]),
                bad_count=int(row[topic.slug + "_bad"]),
                rating_total=int(row[topic.slug + "_sum"]),
            )
            for topic in TOPICS
        ),
    )


def month_topic_totals(
    start: datetime, end: datetime, previous_start: datetime
) -> tuple[MonthTopicTotals, ...]:
    """Per topic the reviews and bad reviews of [start, end) and the reviews of the month before."""
    in_month = Q(created_at__gte=start, created_at__lt=end)
    before = Q(created_at__gte=previous_start, created_at__lt=start)
    aggregates: dict[str, Any] = {}
    for topic in TOPICS:
        condition = topic_condition(topic)
        aggregates[topic.slug + "_n"] = Count("id", filter=condition & in_month)
        aggregates[topic.slug + "_bad"] = Count("id", filter=condition & in_month & _bad())
        aggregates[topic.slug + "_prev"] = Count("id", filter=condition & before)
    row = Review.objects.aggregate(**aggregates)
    return tuple(
        MonthTopicTotals(
            slug=topic.slug,
            review_count=int(row[topic.slug + "_n"]),
            bad_count=int(row[topic.slug + "_bad"]),
            previous_count=int(row[topic.slug + "_prev"]),
        )
        for topic in TOPICS
    )

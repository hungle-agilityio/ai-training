from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction

from reviews.models import Branch, Review
from reviews.search_text import normalize_for_search

# (location id, date cut to the minute, rating, text)
ReviewKey = tuple[int, datetime, int, str]


@dataclass(frozen=True)
class NewReview:
    branch_id: int
    rating: int
    text: str
    created_at: datetime


def minute_of(moment: datetime) -> datetime:
    """The moment cut to the minute, the precision a duplicate is judged at."""
    return moment.replace(second=0, microsecond=0)


def location_ids_by_name() -> dict[str, int]:
    """Lower case location name to id; for the same name the lowest id wins."""
    ids: dict[str, int] = {}
    for pk, name in Branch.objects.order_by("id").values_list("id", "name"):
        ids.setdefault(name.casefold(), pk)
    return ids


def existing_keys(branch_ids: set[int], earliest: datetime, latest: datetime) -> set[ReviewKey]:
    """Keys of the reviews already saved for these locations in the date range (one query)."""
    rows = Review.objects.filter(
        branch_id__in=branch_ids,
        created_at__gte=minute_of(earliest),
        created_at__lt=minute_of(latest) + timedelta(minutes=1),
    ).values_list("branch_id", "created_at", "rating", "text")
    return {(branch_id, minute_of(at), rating, text) for branch_id, at, rating, text in rows}


def save_new_reviews(reviews: Iterable[NewReview]) -> int:
    """Save all reviews in one transaction, with the search copy filled as `create_review` does."""
    objects = [
        Review(
            branch_id=item.branch_id,
            rating=item.rating,
            text=item.text,
            search_text=normalize_for_search(item.text),
            created_at=item.created_at,
        )
        for item in reviews
    ]
    with transaction.atomic():
        return len(Review.objects.bulk_create(objects))

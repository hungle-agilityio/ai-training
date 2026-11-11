from datetime import datetime

from django.db.models import Q

from reviews.repositories import BAD_RATINGS, upsert_followup

# The stored value of the status that a bad review has when nothing is stored.
OPEN = "open"


def save_followup(
    *, review_id: int, status: str, note: str, user_id: int | None, now: datetime
) -> None:
    """One case per review: create it, or update its status, note, user and time; last save wins."""
    upsert_followup(review_id=review_id, status=status, note=note, user_id=user_id, now=now)


def status_filter(status: str) -> Q:
    """Bad reviews in a status; a bad review with no stored case is open."""
    bad = Q(rating__range=BAD_RATINGS)
    if status == OPEN:
        return bad & (Q(followup__isnull=True) | Q(followup__status=OPEN))
    return bad & Q(followup__status=status)

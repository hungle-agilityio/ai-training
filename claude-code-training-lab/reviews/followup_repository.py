from datetime import datetime

from django.db.models import Q

from reviews.models import ReviewFollowUp
from reviews.repositories import BAD_RATINGS

# The stored value of the status that a bad review has when nothing is stored.
OPEN = "open"


def save_followup(
    *, review_id: int, status: str, note: str, user_id: int | None, now: datetime
) -> None:
    """One case per review: create it, or update its status, note, user and time."""
    updated = ReviewFollowUp.objects.filter(review_id=review_id).update(
        status=status, note=note, updated_by_id=user_id, updated_at=now
    )
    if not updated:
        ReviewFollowUp.objects.create(
            review_id=review_id,
            status=status,
            note=note,
            updated_by_id=user_id,
            updated_at=now,
        )


def status_filter(status: str) -> Q:
    """Bad reviews in a status; a bad review with no stored case is open."""
    bad = Q(rating__range=BAD_RATINGS)
    if status == OPEN:
        return bad & (Q(followup__isnull=True) | Q(followup__status=OPEN))
    return bad & Q(followup__status=status)

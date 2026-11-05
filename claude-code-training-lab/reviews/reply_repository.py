from datetime import datetime

from reviews.models import Review, ReviewReply


def save_reply(*, review_id: int, text: str, user_id: int | None, now: datetime) -> None:
    """One reply per review: create it, or update text, user and time and keep created_at."""
    updated = ReviewReply.objects.filter(review_id=review_id).update(
        text=text, replied_by_id=user_id, updated_at=now
    )
    if not updated:
        ReviewReply.objects.create(
            review_id=review_id,
            text=text,
            replied_by_id=user_id,
            created_at=now,
            updated_at=now,
        )


def review_with_reply(review_id: int) -> Review | None:
    """The review, its location, its reply and the reply's user in one query."""
    return (
        Review.objects.select_related("branch", "reply", "reply__replied_by")
        .filter(pk=review_id)
        .first()
    )

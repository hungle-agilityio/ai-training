from datetime import datetime

from django.db.models import Case, IntegerField, QuerySet, Value, When

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


def reviews_without_reply() -> QuerySet[Review]:
    """Reviews with no reply: ratings 1-2, then 3, then 4-5; oldest first, then lowest id."""
    group = Case(
        When(rating__lte=2, then=Value(0)),
        When(rating=3, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    return (
        Review.objects.filter(reply__isnull=True)
        .select_related("branch", "reply")
        .annotate(reply_group=group)
        .order_by("reply_group", "created_at", "id")
    )


def review_with_branch(review_id: int) -> Review | None:
    """The review and its location in one query."""
    return Review.objects.select_related("branch").filter(pk=review_id).first()


def review_with_reply(review_id: int) -> Review | None:
    """The review, its location, its reply and the reply's user in one query."""
    return (
        Review.objects.select_related("branch", "reply", "reply__replied_by")
        .filter(pk=review_id)
        .first()
    )

from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from reviews import reply_repository

REPLY_MAX_LENGTH = 1000


@dataclass(frozen=True)
class ReplyInfo:
    text: str
    updated_at: datetime
    replied_by: str | None


@dataclass(frozen=True)
class ReplyTarget:
    review_id: int
    branch_id: int
    branch_name: str
    rating: int
    rating_percent: int
    text: str
    created_at: datetime
    reply: ReplyInfo | None


def clean_reply_text(text: str) -> str | None:
    """Trimmed text, or None when it is empty or longer than 1000 characters."""
    cleaned = text.strip()
    if not cleaned or len(cleaned) > REPLY_MAX_LENGTH:
        return None
    return cleaned


def reply_target(review_id: int) -> ReplyTarget | None:
    review = reply_repository.review_with_reply(review_id)
    if review is None:
        return None
    info: ReplyInfo | None = None
    try:
        reply = review.reply
    except ObjectDoesNotExist:
        reply = None
    if reply is not None:
        user = reply.replied_by
        info = ReplyInfo(
            text=reply.text,
            updated_at=reply.updated_at,
            replied_by=user.get_username() if user is not None else None,
        )
    return ReplyTarget(
        review_id=review.id,
        branch_id=review.branch_id,
        branch_name=review.branch.name,
        rating=review.rating,
        rating_percent=round(review.rating / 5 * 100),
        text=review.text,
        created_at=review.created_at,
        reply=info,
    )


def save_reply(review_id: int, text: str, user_id: int | None, now: datetime) -> bool:
    """Save the cleaned text; False and nothing saved for an unknown review or a bad text."""
    cleaned = clean_reply_text(text)
    if cleaned is None or reply_repository.review_with_reply(review_id) is None:
        return False
    reply_repository.save_reply(review_id=review_id, text=cleaned, user_id=user_id, now=now)
    return True

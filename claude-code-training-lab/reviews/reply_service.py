from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator

from reviews import reply_repository
from reviews.services import (
    REVIEWS_PER_PAGE,
    PageLink,
    ReviewRow,
    page_href,
    to_review_row,
)

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


@dataclass(frozen=True)
class RepliesPage:
    rows: list[ReviewRow]
    number: int
    num_pages: int
    total: int
    start_index: int
    end_index: int
    has_previous: bool
    has_next: bool
    links: list[PageLink]
    previous_href: str
    next_href: str


def replies_page(page: int | None) -> RepliesPage:
    """One page of the reviews that still need a reply; a wrong page gives the nearest one."""
    paginator = Paginator(reply_repository.reviews_without_reply(), REVIEWS_PER_PAGE)
    current = paginator.get_page(page or 1)
    links = [
        PageLink(
            number=item if isinstance(item, int) else None,
            is_current=item == current.number,
            href=page_href([], item) if isinstance(item, int) else "",
        )
        for item in paginator.get_elided_page_range(current.number, on_each_side=1, on_ends=1)
    ]
    return RepliesPage(
        rows=[to_review_row(review) for review in current.object_list],
        number=current.number,
        num_pages=paginator.num_pages,
        total=paginator.count,
        start_index=current.start_index(),
        end_index=current.end_index(),
        has_previous=current.has_previous(),
        has_next=current.has_next(),
        links=links,
        previous_href=page_href([], max(current.number - 1, 1)),
        next_href=page_href([], min(current.number + 1, paginator.num_pages)),
    )


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

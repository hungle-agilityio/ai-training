from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext

from reviews import reply_repository, reply_service
from reviews.models import Branch, Business, Review, ReviewReply

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)


def make_review(rating: int = 4, text: str = "Great") -> Review:
    business = Business.objects.create(name="Biz")
    branch = Branch.objects.create(business=business, name="Clinic A")
    return Review.objects.create(branch=branch, rating=rating, text=text, created_at=NOW)


def make_user(username: str = "anna") -> int:
    return int(get_user_model().objects.create_user(username=username, password="x").pk)


def test_reply_is_reachable_from_review_with_related_name() -> None:
    review = make_review()
    ReviewReply.objects.create(review=review, text="Thanks", created_at=NOW, updated_at=NOW)
    assert ReviewReply.objects.get(review=review).review_id == review.id
    assert Review.objects.get(pk=review.id).reply.text == "Thanks"


def test_review_cannot_have_two_replies() -> None:
    review = make_review()
    ReviewReply.objects.create(review=review, text="a", created_at=NOW, updated_at=NOW)
    with pytest.raises(IntegrityError):
        ReviewReply.objects.create(review=review, text="b", created_at=NOW, updated_at=NOW)


def test_repository_creates_reply() -> None:
    review = make_review()
    user_id = make_user()
    reply_repository.save_reply(review_id=review.id, text="Thanks", user_id=user_id, now=NOW)
    reply = ReviewReply.objects.get(review=review)
    assert (reply.text, reply.replied_by_id, reply.created_at, reply.updated_at) == (
        "Thanks",
        user_id,
        NOW,
        NOW,
    )


def test_repository_update_keeps_created_at_and_one_reply() -> None:
    review = make_review()
    first = make_user("anna")
    second = make_user("bob")
    later = NOW + timedelta(hours=2)
    reply_repository.save_reply(review_id=review.id, text="One", user_id=first, now=NOW)
    reply_repository.save_reply(review_id=review.id, text="Two", user_id=second, now=later)
    assert ReviewReply.objects.filter(review=review).count() == 1
    reply = ReviewReply.objects.get(review=review)
    assert (reply.text, reply.replied_by_id) == ("Two", second)
    assert reply.created_at == NOW
    assert reply.updated_at == later


def test_deleting_review_deletes_reply() -> None:
    review = make_review()
    reply_repository.save_reply(review_id=review.id, text="Thanks", user_id=None, now=NOW)
    review.delete()
    assert ReviewReply.objects.count() == 0


def test_deleting_user_keeps_reply_with_no_user() -> None:
    review = make_review()
    user_id = make_user()
    reply_repository.save_reply(review_id=review.id, text="Thanks", user_id=user_id, now=NOW)
    get_user_model().objects.filter(pk=user_id).delete()
    assert ReviewReply.objects.get(review=review).replied_by_id is None
    target = reply_service.reply_target(review.id)
    assert target is not None and target.reply is not None
    assert target.reply.replied_by is None


def test_reply_target_without_reply() -> None:
    review = make_review(rating=3, text="Okay")
    target = reply_service.reply_target(review.id)
    assert target == reply_service.ReplyTarget(
        review_id=review.id,
        branch_id=review.branch_id,
        branch_name="Clinic A",
        rating=3,
        rating_percent=60,
        text="Okay",
        created_at=NOW,
        reply=None,
    )


def test_reply_target_with_reply_and_user_name() -> None:
    review = make_review()
    user_id = make_user("anna")
    reply_repository.save_reply(review_id=review.id, text="Thanks", user_id=user_id, now=NOW)
    target = reply_service.reply_target(review.id)
    assert target is not None
    assert target.reply == reply_service.ReplyInfo(text="Thanks", updated_at=NOW, replied_by="anna")


def test_reply_target_missing_review_is_none() -> None:
    assert reply_service.reply_target(999) is None


def test_reply_target_uses_one_query() -> None:
    review = make_review()
    user_id = make_user()
    reply_repository.save_reply(review_id=review.id, text="Thanks", user_id=user_id, now=NOW)
    with CaptureQueriesContext(connection) as ctx:
        reply_service.reply_target(review.id)
    assert len(ctx) == 1


def test_reply_target_without_reply_uses_one_query() -> None:
    review = make_review()
    with CaptureQueriesContext(connection) as ctx:
        reply_service.reply_target(review.id)
    assert len(ctx) == 1


def test_service_save_reply_saves_cleaned_text() -> None:
    review = make_review()
    assert reply_service.save_reply(review.id, "  Thanks \n", None, NOW) is True
    assert ReviewReply.objects.get(review=review).text == "Thanks"


@pytest.mark.parametrize("text", ["   ", "a" * 1001])
def test_service_save_reply_rejects_invalid_text(text: str) -> None:
    review = make_review()
    assert reply_service.save_reply(review.id, text, None, NOW) is False
    assert ReviewReply.objects.count() == 0


def test_service_save_reply_accepts_1000_characters() -> None:
    review = make_review()
    assert reply_service.save_reply(review.id, "a" * 1000, None, NOW) is True


def test_service_save_reply_unknown_review_is_false() -> None:
    assert reply_service.save_reply(999, "Thanks", None, NOW) is False
    assert ReviewReply.objects.count() == 0

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command

from reviews.models import Review, ReviewReply

BAD_REPLY_TEXT = "We are sorry about your visit. Our manager will call you to make it right."


def seed() -> None:
    call_command("seed_demo_data", stdout=StringIO())


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("branch", "text", "hours"),
    [
        ("Airport", "Front desk understaffed, queue out the door.", 30),
        ("Riverside", "Phone line always busy, could not book.", 3),
        ("Riverside", "Nhân viên lễ tân chưa nhiệt tình", 20),
    ],
)
def test_bad_review_reply_comes_after_a_fixed_delay(branch: str, text: str, hours: int) -> None:
    seed()

    review = Review.objects.get(branch__name=branch, text=text)
    reply = ReviewReply.objects.get(review=review)
    assert reply.text == BAD_REPLY_TEXT
    assert reply.replied_by is None
    assert reply.created_at == review.created_at + timedelta(hours=hours)
    assert reply.updated_at == reply.created_at


@pytest.mark.django_db
@pytest.mark.parametrize(
    "text",
    ["Waited 50 minutes, nobody apologized.", "Billing mistake and nobody called back."],
)
def test_other_airport_bad_reviews_stay_without_a_reply(text: str) -> None:
    seed()

    review = Review.objects.get(branch__name="Airport", text=text)
    assert not ReviewReply.objects.filter(review=review).exists()

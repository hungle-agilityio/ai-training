from io import StringIO

import pytest
from django.core.management import call_command

from reviews.models import Review, ReviewReply

REPLY_TEXT = "Thank you for your kind words. We hope to see you again soon."
DEFAULT_REPLY_COUNT = 6
EXTRA_BRANCH_REPLY_COUNT = 2  # ratings 4 and 5 of each extra branch


def seed(*args: str) -> None:
    call_command("seed_demo_data", *args, stdout=StringIO())


@pytest.mark.django_db
def test_default_seed_replies_to_every_good_review_only() -> None:
    seed()

    assert ReviewReply.objects.count() == DEFAULT_REPLY_COUNT
    replied = set(ReviewReply.objects.values_list("review_id", flat=True))
    good = set(Review.objects.filter(rating__gte=4).values_list("id", flat=True))
    assert replied == good


@pytest.mark.django_db
def test_seeded_reply_has_the_fixed_text_no_author_and_the_seed_time() -> None:
    seed()

    for reply in ReviewReply.objects.all():
        assert reply.text == REPLY_TEXT
        assert reply.replied_by is None
        assert reply.updated_at >= reply.review.created_at


@pytest.mark.django_db
def test_extra_branches_follow_the_same_reply_rule() -> None:
    seed("--branches", "2")

    assert ReviewReply.objects.count() == DEFAULT_REPLY_COUNT + 2 * EXTRA_BRANCH_REPLY_COUNT
    assert not ReviewReply.objects.filter(review__rating__lte=3).exists()


@pytest.mark.django_db
def test_seeding_twice_still_gives_six_replies() -> None:
    seed()
    seed()

    assert ReviewReply.objects.count() == DEFAULT_REPLY_COUNT

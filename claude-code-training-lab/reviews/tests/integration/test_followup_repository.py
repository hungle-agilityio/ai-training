from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from reviews import followup, followup_repository
from reviews.models import Branch, Business, Review, ReviewFollowUp
from reviews.repositories import create_review

FIRST = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 3, 15, 30, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    business = Business.objects.create(name="Demo Clinics")
    return Branch.objects.create(business=business, name="Riverside")


def review_of(branch: Branch, rating: int) -> Review:
    return create_review(branch=branch, rating=rating, text=f"{rating} stars", created_at=FIRST)


def matching(status: str) -> set[int]:
    reviews = Review.objects.filter(followup_repository.status_filter(status))
    return set(reviews.values_list("id", flat=True))


def test_stored_statuses_are_the_statuses_of_the_rule() -> None:
    stored = [value for value, _ in ReviewFollowUp.STATUS_CHOICES]

    assert stored == list(followup.STATUS_LABELS)
    assert followup_repository.OPEN == followup.STATUS_OPEN


def test_save_creates_the_case_of_a_review(branch: Branch) -> None:
    review = review_of(branch, 2)
    user = get_user_model().objects.create_user(username="staff")

    followup_repository.save_followup(
        review_id=review.id, status="contacted", note="Called back.", user_id=user.id, now=FIRST
    )

    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_by, case.updated_at) == (
        "contacted",
        "Called back.",
        user,
        FIRST,
    )
    assert review.followup == case


def test_save_again_updates_the_one_case(branch: Branch) -> None:
    review = review_of(branch, 1)
    user = get_user_model().objects.create_user(username="staff")
    followup_repository.save_followup(
        review_id=review.id, status="contacted", note="Called back.", user_id=user.id, now=FIRST
    )

    followup_repository.save_followup(
        review_id=review.id, status="resolved", note="", user_id=None, now=LATER
    )

    case = ReviewFollowUp.objects.get()
    assert case.review_id == review.id
    assert (case.status, case.note, case.updated_by, case.updated_at) == (
        "resolved",
        "",
        None,
        LATER,
    )


def test_save_changes_only_the_case_of_that_review(branch: Branch) -> None:
    first = review_of(branch, 1)
    second = review_of(branch, 2)
    followup_repository.save_followup(
        review_id=first.id, status="contacted", note="one", user_id=None, now=FIRST
    )

    followup_repository.save_followup(
        review_id=second.id, status="resolved", note="two", user_id=None, now=LATER
    )

    stored = ReviewFollowUp.objects.order_by("review_id").values_list("review_id", "status", "note")
    assert list(stored) == [(first.id, "contacted", "one"), (second.id, "resolved", "two")]


def test_save_uses_a_fixed_number_of_queries(branch: Branch) -> None:
    review = review_of(branch, 2)

    with CaptureQueriesContext(connection) as creating:
        followup_repository.save_followup(
            review_id=review.id, status="contacted", note="", user_id=None, now=FIRST
        )
    with CaptureQueriesContext(connection) as updating:
        followup_repository.save_followup(
            review_id=review.id, status="resolved", note="", user_id=None, now=LATER
        )

    assert len(creating) == 2
    assert len(updating) == 1


def test_the_case_goes_with_its_review(branch: Branch) -> None:
    review = review_of(branch, 2)
    followup_repository.save_followup(
        review_id=review.id, status="contacted", note="", user_id=None, now=FIRST
    )

    review.delete()

    assert not ReviewFollowUp.objects.exists()


def test_the_case_stays_without_a_user_when_the_user_is_deleted(branch: Branch) -> None:
    review = review_of(branch, 2)
    user = get_user_model().objects.create_user(username="staff")
    followup_repository.save_followup(
        review_id=review.id, status="contacted", note="kept", user_id=user.id, now=FIRST
    )

    user.delete()

    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_by) == ("contacted", "kept", None)


def test_open_keeps_bad_reviews_with_no_case_or_a_stored_open(branch: Branch) -> None:
    no_case = review_of(branch, 1)
    stored_open = review_of(branch, 2)
    contacted = review_of(branch, 2)
    resolved = review_of(branch, 1)
    for review, status in (
        (stored_open, "open"),
        (contacted, "contacted"),
        (resolved, "resolved"),
    ):
        followup_repository.save_followup(
            review_id=review.id, status=status, note="", user_id=None, now=FIRST
        )

    assert matching("open") == {no_case.id, stored_open.id}
    assert matching("contacted") == {contacted.id}
    assert matching("resolved") == {resolved.id}


@pytest.mark.parametrize("status", ["open", "contacted", "resolved"])
def test_three_to_five_star_reviews_never_match(branch: Branch, status: str) -> None:
    for rating in (3, 4, 5):
        review = review_of(branch, rating)
        followup_repository.save_followup(
            review_id=review.id, status=status, note="", user_id=None, now=FIRST
        )
        review_of(branch, rating)

    assert matching(status) == set()


def test_the_filter_adds_no_query(branch: Branch) -> None:
    for status in ("open", "contacted"):
        review = review_of(branch, 2)
        followup_repository.save_followup(
            review_id=review.id, status=status, note="", user_id=None, now=FIRST
        )
    review_of(branch, 1)

    with CaptureQueriesContext(connection) as queries:
        found = list(Review.objects.filter(followup_repository.status_filter("open")))

    assert len(found) == 2
    assert len(queries) == 1

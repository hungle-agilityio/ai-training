from io import StringIO

import pytest
from django.core.management import call_command

from reviews import followup_repository
from reviews.models import Review, ReviewFollowUp


def seed() -> None:
    call_command("seed_demo_data", stdout=StringIO())


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("text", "status", "note"),
    [
        (
            "Phone line always busy, could not book.",
            "contacted",
            "Called the customer back and booked a visit for the next morning.",
        ),
        (
            "Nhân viên lễ tân chưa nhiệt tình",
            "resolved",
            "Talked with the front desk team about greeting every customer.",
        ),
    ],
)
def test_riverside_bad_review_gets_a_demo_case(text: str, status: str, note: str) -> None:
    seed()

    case = ReviewFollowUp.objects.get(review__branch__name="Riverside", review__text=text)
    assert (case.status, case.note, case.updated_by) == (status, note, None)


@pytest.mark.django_db
def test_only_the_two_demo_cases_are_stored() -> None:
    seed()

    assert ReviewFollowUp.objects.count() == 2


@pytest.mark.django_db
def test_the_three_bad_airport_reviews_stay_open() -> None:
    seed()

    airport_bad = Review.objects.filter(branch__name="Airport", rating__lte=2)
    still_open = Review.objects.filter(followup_repository.status_filter("open"))
    assert airport_bad.count() == 3
    assert not ReviewFollowUp.objects.filter(review__branch__name="Airport").exists()
    assert set(still_open) == set(airport_bad)


@pytest.mark.django_db
def test_seeding_again_removes_the_old_cases() -> None:
    seed()
    extra = Review.objects.filter(branch__name="Airport", rating__lte=2).first()
    assert extra is not None
    followup_repository.save_followup(
        review_id=extra.id,
        status="resolved",
        note="left over",
        user_id=None,
        now=extra.created_at,
    )

    seed()

    assert ReviewFollowUp.objects.count() == 2
    assert not ReviewFollowUp.objects.filter(note="left over").exists()


@pytest.mark.django_db
def test_extra_branches_get_no_case() -> None:
    call_command("seed_demo_data", "--branches", "2", "--with-new-branch", stdout=StringIO())

    assert ReviewFollowUp.objects.count() == 2

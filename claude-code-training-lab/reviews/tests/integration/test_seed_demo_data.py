from io import StringIO

import pytest
from django.core.management import call_command

from reviews.models import Branch, Business, Review

DEFAULT_BRANCHES = {"Airport", "Downtown", "Riverside"}
DEFAULT_REVIEW_COUNT = 10


def seed(*args: str) -> str:
    out = StringIO()
    call_command("seed_demo_data", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_default_seed_creates_one_business_three_locations_and_ten_reviews() -> None:
    seed()

    assert Business.objects.count() == 1
    assert set(Branch.objects.values_list("name", flat=True)) == DEFAULT_BRANCHES
    assert Review.objects.count() == DEFAULT_REVIEW_COUNT


@pytest.mark.django_db
def test_seeded_ratings_are_between_one_and_five_and_every_review_has_text() -> None:
    seed()

    assert all(1 <= review.rating <= 5 for review in Review.objects.all())
    assert all(review.text for review in Review.objects.all())


@pytest.mark.django_db
def test_seeded_reviews_of_a_location_have_different_dates_newest_first() -> None:
    seed()

    dates = list(
        Review.objects.filter(branch__name="Airport")
        .order_by("-created_at")
        .values_list("created_at", flat=True)
    )

    assert len(dates) == len(set(dates)) == 4


@pytest.mark.django_db
def test_branches_option_adds_extra_locations_with_three_reviews_each() -> None:
    seed("--branches", "2")

    extra = Branch.objects.filter(name__startswith="Extra ")
    assert sorted(extra.values_list("name", flat=True)) == ["Extra 1", "Extra 2"]
    assert Review.objects.filter(branch__in=extra).count() == 6
    assert Review.objects.count() == DEFAULT_REVIEW_COUNT + 6


@pytest.mark.django_db
def test_with_new_branch_adds_a_location_without_reviews() -> None:
    seed("--with-new-branch")

    newtown = Branch.objects.get(name="Newtown")
    assert newtown.reviews.count() == 0
    assert Review.objects.count() == DEFAULT_REVIEW_COUNT


@pytest.mark.django_db
def test_seeding_twice_replaces_the_data_instead_of_adding_to_it() -> None:
    seed()
    first_ids = set(Branch.objects.values_list("id", flat=True))

    seed()

    assert Business.objects.count() == 1
    assert Branch.objects.count() == len(DEFAULT_BRANCHES)
    assert Review.objects.count() == DEFAULT_REVIEW_COUNT
    assert not first_ids & set(Branch.objects.values_list("id", flat=True))


@pytest.mark.django_db
def test_seed_deletes_data_that_was_there_before() -> None:
    old = Business.objects.create(name="Old business")
    Branch.objects.create(business=old, name="Old branch")

    seed()

    assert not Business.objects.filter(name="Old business").exists()
    assert not Branch.objects.filter(name="Old branch").exists()


@pytest.mark.django_db
def test_seed_reports_how_many_locations_it_created() -> None:
    message = seed("--branches", "1", "--with-new-branch")

    assert "Seeded 5 branches." in message

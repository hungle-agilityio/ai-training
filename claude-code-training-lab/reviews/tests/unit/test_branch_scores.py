from datetime import UTC, datetime

import pytest
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review
from reviews.repositories import branch_rating_totals
from reviews.services import branch_scores


def _add_branch(business: Business, name: str, ratings: tuple[int, ...]) -> Branch:
    branch = Branch.objects.create(business=business, name=name)
    created_at = datetime(2026, 10, 14, tzinfo=UTC)
    Review.objects.bulk_create(
        Review(branch=branch, rating=rating, text="ok", created_at=created_at) for rating in ratings
    )
    return branch


@pytest.mark.django_db
@pytest.mark.parametrize("branch_count", [20, 200])
def test_branch_scores_use_one_query(
    branch_count: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    # Bug #1: 503 locations used to need 504 lookups
    business = Business.objects.create(name="Demo")
    for index in range(branch_count):
        _add_branch(business, f"Branch {index}", (4, 5, 3))

    with django_assert_num_queries(1):
        scores = branch_scores()

    assert len(scores) == branch_count


@pytest.mark.django_db
def test_branch_scores_round_half_up() -> None:
    # (2, 2, 2, 3) is 2.25: half up gives 2.3, while Avg() with round() would give 2.2
    _add_branch(Business.objects.create(name="Demo"), "Airport", (2, 2, 2, 3))

    assert branch_scores()[0].average_rating == 2.3


@pytest.mark.django_db
def test_branch_score_average_is_a_float() -> None:
    _add_branch(Business.objects.create(name="Demo"), "Airport", (4, 4))

    average = branch_scores()[0].average_rating

    assert isinstance(average, float)
    assert average == 4.0


@pytest.mark.django_db
def test_branch_scores_are_ordered_by_id() -> None:
    business = Business.objects.create(name="Demo")
    first = _add_branch(business, "Zeta", (5,))
    second = _add_branch(business, "Alpha", (1,))

    assert [score.branch_id for score in branch_scores()] == [first.id, second.id]


@pytest.mark.django_db
def test_branch_without_reviews_has_no_average_and_does_not_raise() -> None:
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Downtown", (4, 4))
    _add_branch(business, "Newtown", ())

    scores = {score.name: score for score in branch_scores()}

    assert scores["Newtown"].review_count == 0
    assert scores["Newtown"].average_rating is None
    assert scores["Downtown"].average_rating == 4.0


@pytest.mark.django_db
def test_branch_totals_are_counted_per_branch() -> None:
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Airport", (1, 2))
    _add_branch(business, "Empty", ())
    _add_branch(business, "Downtown", (5, 5, 4))

    totals = {row.name: (row.review_count, row.rating_total) for row in branch_rating_totals()}

    assert totals == {"Airport": (2, 3), "Empty": (0, 0), "Downtown": (3, 14)}

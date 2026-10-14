from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review


@pytest.mark.django_db
def test_dashboard_lists_branch_with_reviews() -> None:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Downtown")
    for rating in (4, 4):
        Review.objects.create(
            branch=branch, rating=rating, text="ok", created_at=datetime(2026, 10, 1, tzinfo=UTC)
        )

    response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert response.json()["branches"][0]["name"] == "Downtown"


def _add_branch(business: Business, name: str, ratings: tuple[int, ...]) -> Branch:
    branch = Branch.objects.create(business=business, name=name)
    Review.objects.bulk_create(
        Review(
            branch=branch, rating=rating, text="ok", created_at=datetime(2026, 10, 1, tzinfo=UTC)
        )
        for rating in ratings
    )
    return branch


@pytest.mark.django_db
def test_dashboard_shows_average_with_one_decimal() -> None:
    # BUG-001: Riverside has ratings 4, 5, 2 and must show 3.7, not 3
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Airport", (2, 2, 3, 1))
    _add_branch(business, "Riverside", (4, 5, 2))

    branches = {item["name"]: item for item in Client().get("/dashboard/").json()["branches"]}

    assert branches["Riverside"]["average_rating"] == 3.7
    assert branches["Riverside"]["review_count"] == 3


@pytest.mark.django_db
def test_dashboard_query_count_does_not_grow_with_branches(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    # BUG-002: 20 branches with 3 reviews each must not need one lookup per branch
    business = Business.objects.create(name="Demo")
    for index in range(20):
        _add_branch(business, f"Branch {index}", (4, 5, 3))

    with django_assert_max_num_queries(3):
        response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert len(response.json()["branches"]) == 20


@pytest.mark.django_db
def test_dashboard_lists_branch_without_reviews() -> None:
    # BUG-003: a new branch with no reviews must not break the whole dashboard
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Downtown", (4, 4))
    _add_branch(business, "Newtown", ())

    response = Client().get("/dashboard/")

    assert response.status_code == 200
    branches = {item["name"]: item for item in response.json()["branches"]}
    assert set(branches) == {"Downtown", "Newtown"}
    assert branches["Newtown"]["review_count"] == 0
    assert branches["Newtown"]["average_rating"] is None
    assert branches["Downtown"]["average_rating"] == 4.0

from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review


@pytest.mark.django_db
def test_dashboard_page_renders_html_for_branches() -> None:
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Downtown", (5, 4))

    response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    content = response.content.decode()
    assert "ReviewRadar" in content
    assert "Downtown" in content


@pytest.mark.django_db
def test_dashboard_page_shows_empty_state_without_branches() -> None:
    response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert "No locations yet" in response.content.decode()


def test_home_redirects_to_dashboard() -> None:
    response = Client().get("/")

    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


@pytest.mark.django_db
def test_dashboard_lists_branch_with_reviews() -> None:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Downtown")
    for rating in (4, 4):
        Review.objects.create(
            branch=branch, rating=rating, text="ok", created_at=datetime(2026, 10, 1, tzinfo=UTC)
        )

    response = Client().get("/api/dashboard/")

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
    # Bug #1: Riverside has ratings 4, 5, 2 and must show 3.7, not 3
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Airport", (2, 2, 3, 1))
    _add_branch(business, "Riverside", (4, 5, 2))

    branches = {item["name"]: item for item in Client().get("/api/dashboard/").json()["branches"]}

    assert branches["Riverside"]["average_rating"] == 3.7
    assert branches["Riverside"]["review_count"] == 3


@pytest.mark.django_db
def test_dashboard_query_count_does_not_grow_with_branches(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    # Bug #2: 20 branches with 3 reviews each must not need one lookup per branch
    business = Business.objects.create(name="Demo")
    for index in range(20):
        _add_branch(business, f"Branch {index}", (4, 5, 3))

    with django_assert_max_num_queries(3):
        response = Client().get("/api/dashboard/")

    assert response.status_code == 200
    assert len(response.json()["branches"]) == 20


@pytest.mark.django_db
def test_dashboard_lists_branch_without_reviews() -> None:
    # Bug #3: a new branch with no reviews must not break the whole dashboard
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Downtown", (4, 4))
    _add_branch(business, "Newtown", ())

    response = Client().get("/api/dashboard/")

    assert response.status_code == 200
    branches = {item["name"]: item for item in response.json()["branches"]}
    assert set(branches) == {"Downtown", "Newtown"}
    assert branches["Newtown"]["review_count"] == 0
    assert branches["Newtown"]["average_rating"] is None
    assert branches["Downtown"]["average_rating"] == 4.0


@pytest.mark.django_db
def test_dashboard_page_shows_riverside_average_of_3_7() -> None:
    # Bug #1: the Location scores table must show 3.7 for Riverside, not 3.0
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Riverside", (4, 5, 2))

    content = Client().get("/dashboard/").content.decode()

    assert "<strong>3.7</strong>" in content
    assert "<strong>3.0</strong>" not in content


@pytest.mark.django_db
@pytest.mark.parametrize("branch_count", [20, 200])
def test_dashboard_page_query_count_does_not_grow_with_branches(
    branch_count: int,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Bug #1: the page needs 3 queries (scores, rating counts, latest reviews) for any number
    business = Business.objects.create(name="Demo")
    for index in range(branch_count):
        _add_branch(business, f"Branch {index}", (4, 5, 3))

    with django_assert_num_queries(3):
        response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert f"Branch {branch_count - 1}" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_page_shows_no_reviews_yet_for_a_new_branch() -> None:
    # A location without reviews is listed with "No reviews yet" instead of an empty score
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Downtown", (4, 4))
    _add_branch(business, "Newtown", ())

    response = Client().get("/dashboard/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Newtown" in content
    assert content.count("No reviews yet") == 1
    assert "<strong>4.0</strong>" in content
    assert "<strong></strong>" not in content
    assert 'aria-label=" out of 5"' not in content
    assert 'class="badge badge-"' not in content


@pytest.mark.django_db
def test_dashboard_api_gives_null_average_for_a_branch_without_reviews() -> None:
    # Contract: "average_rating" is null (not a number) for a location without reviews
    business = Business.objects.create(name="Demo")
    _add_branch(business, "Newtown", ())

    branch = Client().get("/api/dashboard/").json()["branches"][0]

    assert branch["review_count"] == 0
    assert branch["average_rating"] is None

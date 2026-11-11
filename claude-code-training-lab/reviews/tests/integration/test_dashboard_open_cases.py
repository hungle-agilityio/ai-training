from datetime import UTC, datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review, ReviewFollowUp, ReviewReply
from reviews.services import dashboard_overview

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def _add_reviews(branch: Branch, ratings: tuple[int, ...]) -> list[Review]:
    return [
        Review.objects.create(branch=branch, rating=rating, text="ok", created_at=NOW)
        for rating in ratings
    ]


def _case(review: Review, status: str) -> None:
    ReviewFollowUp.objects.create(review=review, status=status, updated_at=NOW)


def _tile(content: str) -> str:
    return content.split('id="kpi-open-cases"')[1].split("</article>")[0]


@pytest.mark.django_db
def test_dashboard_counts_open_cases_of_bad_reviews_across_locations() -> None:
    business = Business.objects.create(name="Demo")
    first = _add_reviews(Branch.objects.create(business=business, name="A"), (1, 2, 2, 5))
    second = _add_reviews(Branch.objects.create(business=business, name="B"), (1, 2, 3))
    _case(first[0], "open")
    _case(first[1], "contacted")
    _case(second[0], "resolved")
    # No stored case counts as Open: first[2] and second[1]

    content = Client().get("/dashboard/").content.decode()

    assert '<article class="kpi" id="kpi-open-cases">' in content
    tile = _tile(content)
    assert "Open cases" in tile
    assert '<p class="kpi-value">3</p>' in tile
    assert "Bad reviews not handled yet" in tile
    assert '<a class="row-link" href="/reviews/?followup=open">See open cases</a>' in tile
    assert "No open cases" not in tile


@pytest.mark.django_db
def test_open_cases_tile_comes_after_replied_in_24h() -> None:
    business = Business.objects.create(name="Demo")
    _add_reviews(Branch.objects.create(business=business, name="A"), (1,))

    content = Client().get("/dashboard/").content.decode()

    after_reply_speed = content.split('id="kpi-reply-speed"')[1].split("</article>", 1)[1]
    assert after_reply_speed.lstrip().startswith('<article class="kpi" id="kpi-open-cases">')


@pytest.mark.django_db
def test_dashboard_says_no_open_cases_at_zero() -> None:
    business = Business.objects.create(name="Demo")
    reviews = _add_reviews(Branch.objects.create(business=business, name="A"), (1, 2, 3, 4, 5))
    _case(reviews[0], "contacted")
    _case(reviews[1], "resolved")

    tile = _tile(Client().get("/dashboard/").content.decode())

    assert '<p class="kpi-value">0</p>' in tile
    assert "No open cases" in tile
    assert "Bad reviews not handled yet" not in tile
    assert "See open cases" not in tile
    assert "followup=open" not in tile


@pytest.mark.django_db
def test_a_case_stored_on_a_review_that_is_not_bad_is_not_counted() -> None:
    business = Business.objects.create(name="Demo")
    reviews = _add_reviews(Branch.objects.create(business=business, name="A"), (3, 5))
    _case(reviews[0], "open")
    _case(reviews[1], "open")

    assert dashboard_overview().open_cases_count == 0


@pytest.mark.django_db
def test_a_reply_does_not_close_an_open_case() -> None:
    business = Business.objects.create(name="Demo")
    (review,) = _add_reviews(Branch.objects.create(business=business, name="A"), (1,))
    ReviewReply.objects.create(review=review, text="Sorry", created_at=NOW, updated_at=NOW)

    assert dashboard_overview().open_cases_count == 1


@pytest.mark.django_db
def test_overview_open_cases_count_is_an_int() -> None:
    business = Business.objects.create(name="Demo")
    _add_reviews(Branch.objects.create(business=business, name="A"), (1, 2, 5))

    count = dashboard_overview().open_cases_count

    assert count == 2
    assert type(count) is int


@pytest.mark.django_db
def test_dashboard_without_locations_has_no_open_cases_tile() -> None:
    content = Client().get("/dashboard/").content.decode()

    assert "No locations yet" in content
    assert "kpi-open-cases" not in content


@pytest.mark.django_db
def test_demo_data_shows_3_open_cases() -> None:
    call_command("seed_demo_data", stdout=StringIO())

    tile = _tile(Client().get("/dashboard/").content.decode())

    assert '<p class="kpi-value">3</p>' in tile
    assert 'href="/reviews/?followup=open"' in tile


@pytest.mark.django_db
@pytest.mark.parametrize("branches", [20, 200])
def test_dashboard_query_count_stays_3_with_open_cases(
    branches: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="Demo")
    for index in range(branches):
        reviews = _add_reviews(
            Branch.objects.create(business=business, name=f"B{index}"), (1, 2, 4)
        )
        _case(reviews[0], "resolved")

    with django_assert_num_queries(3):
        response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert f'<p class="kpi-value">{branches}</p>' in _tile(response.content.decode())


@pytest.mark.django_db
def test_dashboard_api_does_not_change() -> None:
    business = Business.objects.create(name="Demo")
    _add_reviews(Branch.objects.create(business=business, name="A"), (1, 2))

    body = Client().get("/api/dashboard/").json()

    assert body == {
        "branches": [
            {
                "branch_id": Branch.objects.get().id,
                "name": "A",
                "review_count": 2,
                "average_rating": 1.5,
            }
        ]
    }

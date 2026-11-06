from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review, ReviewReply
from reviews.services import dashboard_overview

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def _add_reviews(branch: Branch, ratings: tuple[int, ...]) -> list[Review]:
    return [
        Review.objects.create(branch=branch, rating=rating, text="ok", created_at=NOW)
        for rating in ratings
    ]


def _reply(review: Review) -> None:
    ReviewReply.objects.create(review=review, text="Thanks", created_at=NOW, updated_at=NOW)


@pytest.mark.django_db
def test_dashboard_counts_reviews_without_a_reply_across_locations() -> None:
    business = Business.objects.create(name="Demo")
    first = _add_reviews(Branch.objects.create(business=business, name="A"), (5, 4, 2))
    second = _add_reviews(Branch.objects.create(business=business, name="B"), (3, 3))
    _reply(first[0])
    _reply(second[1])

    content = Client().get("/dashboard/").content.decode()

    assert 'id="kpi-needs-reply"' in content
    tile = content.split('id="kpi-needs-reply"')[1].split("</article>")[0]
    assert "Need a reply" in tile
    assert '<p class="kpi-value">3</p>' in tile
    assert "Reviews with no reply yet" in tile
    assert 'href="/replies/"' in tile
    assert "Open reply drafts" in tile


@pytest.mark.django_db
def test_dashboard_says_every_review_has_a_reply_at_zero() -> None:
    business = Business.objects.create(name="Demo")
    for review in _add_reviews(Branch.objects.create(business=business, name="A"), (5, 4)):
        _reply(review)

    content = Client().get("/dashboard/").content.decode()

    tile = content.split('id="kpi-needs-reply"')[1].split("</article>")[0]
    assert '<p class="kpi-value">0</p>' in tile
    assert "Every review has a reply" in tile


@pytest.mark.django_db
def test_dashboard_without_locations_has_no_reply_tile() -> None:
    content = Client().get("/dashboard/").content.decode()

    assert "No locations yet" in content
    assert "kpi-needs-reply" not in content


@pytest.mark.django_db
def test_overview_needs_reply_count_is_an_int() -> None:
    business = Business.objects.create(name="Demo")
    _add_reviews(Branch.objects.create(business=business, name="A"), (5, 1))

    count = dashboard_overview().needs_reply_count

    assert count == 2
    assert type(count) is int


@pytest.mark.django_db
@pytest.mark.parametrize("branches", [20, 200])
def test_dashboard_query_count_stays_3_with_replies(
    branches: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="Demo")
    for index in range(branches):
        reviews = _add_reviews(Branch.objects.create(business=business, name=f"B{index}"), (4, 2))
        _reply(reviews[0])

    with django_assert_num_queries(3):
        response = Client().get("/dashboard/")

    assert response.status_code == 200
    assert (
        f'<p class="kpi-value">{branches}</p>'
        in response.content.decode().split('id="kpi-needs-reply"')[1]
    )

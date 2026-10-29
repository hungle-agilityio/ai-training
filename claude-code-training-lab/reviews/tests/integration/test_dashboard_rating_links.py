from datetime import UTC, datetime

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from reviews.models import Branch, Business, Review


def _make_reviews(ratings: list[int]) -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")
    for rating in ratings:
        Review.objects.create(
            branch=branch, rating=rating, text="x", created_at=datetime(2026, 10, 1, tzinfo=UTC)
        )


@pytest.mark.django_db
def test_every_breakdown_line_links_to_its_rating_even_with_zero_reviews() -> None:
    _make_reviews([5, 2, 2])

    content = Client().get("/dashboard/").content.decode()

    for stars in (5, 4, 3, 2, 1):
        assert f'href="/reviews/?rating={stars}"' in content


@pytest.mark.django_db
def test_link_has_an_accessible_name_with_the_count() -> None:
    _make_reviews([5, 2, 2])

    content = Client().get("/dashboard/").content.decode()

    assert 'aria-label="Show 2-star reviews (2)"' in content
    assert 'aria-label="Show 1-star reviews (0)"' in content


@pytest.mark.django_db
def test_link_target_shows_only_that_rating_and_selects_it() -> None:
    _make_reviews([2, 2, 2, 2, 1])

    content = Client().get("/reviews/?rating=2").content.decode()

    assert '<option value="2" selected>' in content
    assert content.count('class="review-row"') == 4


@pytest.mark.django_db
def test_zero_review_rating_shows_empty_message_with_rating_selected() -> None:
    _make_reviews([5])

    content = Client().get("/reviews/?rating=1").content.decode()

    assert "No reviews found" in content
    assert '<option value="1" selected>' in content


@pytest.mark.django_db
def test_dashboard_query_count_does_not_depend_on_rating_links() -> None:
    _make_reviews([5, 4, 3, 2, 1])
    client = Client()
    with CaptureQueriesContext(connection) as many:
        client.get("/dashboard/")
    _make_reviews([5, 4, 3, 2, 1])
    with CaptureQueriesContext(connection) as more:
        client.get("/dashboard/")

    assert len(more) == len(many)

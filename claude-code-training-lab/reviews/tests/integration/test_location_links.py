from datetime import UTC, datetime

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from reviews.models import Branch, Business, Review


def _make_branches() -> tuple[Branch, Branch]:
    business = Business.objects.create(name="Demo")
    riverside = Branch.objects.create(business=business, name="Riverside")
    newtown = Branch.objects.create(business=business, name="Newtown")
    Review.objects.create(
        branch=riverside, rating=5, text="Great", created_at=datetime(2026, 10, 1, tzinfo=UTC)
    )
    return riverside, newtown


@pytest.mark.django_db
def test_dashboard_has_details_column_and_link_for_every_location() -> None:
    riverside, newtown = _make_branches()

    content = Client().get("/dashboard/").content.decode()

    assert '<th scope="col">Details</th>' in content
    for branch in (riverside, newtown):
        assert f'href="/locations/{branch.id}/"' in content
        assert f'aria-label="Details for {branch.name}"' in content
    assert content.count(">Details</a>") == 2


@pytest.mark.django_db
def test_dashboard_name_links_and_latest_reviews_stay_the_same() -> None:
    riverside, _ = _make_branches()

    content = Client().get("/dashboard/").content.decode()

    assert f'href="/reviews/?location={riverside.id}"' in content
    assert "<strong>Riverside</strong>" in content
    assert content.count("/locations/") == 2


@pytest.mark.django_db
def test_reviews_page_location_name_links_to_location_page() -> None:
    riverside, _ = _make_branches()

    content = Client().get("/reviews/").content.decode()

    assert f'<a class="row-link" href="/locations/{riverside.id}/">Riverside</a>' in content


@pytest.mark.django_db
def test_dashboard_query_count_is_unchanged() -> None:
    _make_branches()

    with CaptureQueriesContext(connection) as queries:
        Client().get("/dashboard/")

    assert len(queries) == 3


@pytest.mark.django_db
def test_reviews_page_query_count_does_not_grow_with_rows() -> None:
    riverside, newtown = _make_branches()
    with CaptureQueriesContext(connection) as before:
        Client().get("/reviews/")
    for i in range(5):
        Review.objects.create(
            branch=newtown, rating=4, text=f"More {i}", created_at=datetime(2026, 10, 2, tzinfo=UTC)
        )

    with CaptureQueriesContext(connection) as after:
        Client().get("/reviews/")

    assert len(after) == len(before)

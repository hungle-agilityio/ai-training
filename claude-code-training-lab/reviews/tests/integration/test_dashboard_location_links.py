from datetime import UTC, datetime

import pytest
from django.test import Client

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
def test_location_names_link_to_filtered_reviews_even_without_reviews() -> None:
    riverside, newtown = _make_branches()

    content = Client().get("/dashboard/").content.decode()

    assert f'href="/reviews/?location={riverside.id}"' in content
    assert f'href="/reviews/?location={newtown.id}"' in content


@pytest.mark.django_db
def test_latest_reviews_names_are_not_links() -> None:
    _make_branches()

    content = Client().get("/dashboard/").content.decode()

    assert content.count("/reviews/?location=") == 2
    assert "<strong>Riverside</strong>" in content


@pytest.mark.django_db
def test_link_target_shows_only_that_location() -> None:
    riverside, newtown = _make_branches()

    content = Client().get(f"/reviews/?location={newtown.id}").content.decode()

    assert "No reviews found" in content
    assert riverside.name in content  # still listed as a filter option

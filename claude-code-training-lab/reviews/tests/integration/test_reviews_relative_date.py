from datetime import timedelta

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from reviews.models import Branch, Business, Review


def _review(branch: Branch, age: timedelta) -> None:
    Review.objects.create(branch=branch, rating=5, text="ok", created_at=timezone.now() - age)


def _branch() -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Demo"), name="A")


@pytest.mark.django_db
def test_reviews_page_shows_relative_text_and_full_date_title() -> None:
    branch = _branch()
    _review(branch, timedelta(days=3))
    _review(branch, timedelta(days=10))
    old = timezone.localtime(timezone.now() - timedelta(days=10))

    content = Client().get("/reviews/").content.decode()

    assert "3 days ago" in content
    assert f">{old:%b} {old.day}, {old:%Y}</time>" in content
    assert 'title="' in content
    assert 'datetime="' in content


@pytest.mark.django_db
def test_reviews_page_query_count_does_not_depend_on_rows() -> None:
    branch = _branch()
    for i in range(3):
        _review(branch, timedelta(hours=i))
    client = Client()

    with CaptureQueriesContext(connection) as small:
        client.get("/reviews/")
    for i in range(10):
        _review(branch, timedelta(hours=i))
    with CaptureQueriesContext(connection) as large:
        client.get("/reviews/")

    assert len(large) == len(small)

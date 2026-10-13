from datetime import UTC, datetime

import pytest
from django.test import Client

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

import unicodedata
from datetime import UTC, datetime

import pytest

from reviews.models import Branch, Business
from reviews.repositories import create_review


@pytest.mark.django_db
def test_create_review_stores_the_normalised_text() -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Airport")
    text = unicodedata.normalize("NFD", "ĐAU CHÂN Đỡ Hẳn")

    review = create_review(
        branch=branch,
        rating=4,
        text=text,
        created_at=datetime(2026, 10, 14, 2, 0, tzinfo=UTC),
    )

    review.refresh_from_db()
    assert review.text == text
    assert review.search_text == unicodedata.normalize("NFC", "đau chân đỡ hẳn")

from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review


def _seed(branches: int, per_branch: int, text: str = "ok") -> None:
    business = Business.objects.create(name="Demo")
    base = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)
    for b in range(branches):
        branch = Branch.objects.create(business=business, name=f"Branch {b}")
        Review.objects.bulk_create(
            Review(
                branch=branch,
                rating=(i % 5) + 1,
                text=text,
                created_at=base - timedelta(minutes=b * per_branch + i),
            )
            for i in range(per_branch)
        )


@pytest.mark.django_db
def test_reviews_page_lists_twenty_reviews_with_summary() -> None:
    _seed(branches=5, per_branch=9)

    response = Client().get("/reviews/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Showing 1-20 of 45 reviews" in content
    assert content.count('class="review-row"') == 20
    for heading in ("Location", "Rating", "Review text", "Sentiment", "Date"):
        assert heading in content


@pytest.mark.django_db
def test_reviews_page_follows_the_page_parameter() -> None:
    _seed(branches=5, per_branch=9)

    content = Client().get("/reviews/?page=3").content.decode()

    assert "Showing 41-45 of 45 reviews" in content
    assert content.count('class="review-row"') == 5


@pytest.mark.django_db
def test_previous_is_disabled_on_first_page_and_next_on_last() -> None:
    _seed(branches=5, per_branch=9)

    first = Client().get("/reviews/").content.decode()
    last = Client().get("/reviews/?page=3").content.decode()

    assert 'aria-disabled="true">Previous' in first
    assert 'href="?page=2"' in first
    assert 'aria-disabled="true">Next' in last
    assert 'href="?page=2"' in last


@pytest.mark.django_db
def test_long_text_is_shortened_and_full_text_is_in_the_page() -> None:
    _seed(branches=1, per_branch=1, text="word " * 40)

    content = Client().get("/reviews/").content.decode()

    assert f'<span class="text-full">{"word " * 40}</span>' in content
    assert 'class="text-short"' in content
    assert "…" in content


@pytest.mark.django_db
def test_short_text_has_no_expandable_part() -> None:
    _seed(branches=1, per_branch=1, text="ok")

    assert "text-full" not in Client().get("/reviews/").content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "summary"),
    [
        ("?page=abc", "Showing 1-20 of 45 reviews"),
        ("?page=0", "Showing 1-20 of 45 reviews"),
        ("?page=-2", "Showing 1-20 of 45 reviews"),
        ("?page=9999", "Showing 41-45 of 45 reviews"),
    ],
)
def test_invalid_page_parameter_falls_back(query: str, summary: str) -> None:
    _seed(branches=5, per_branch=9)

    response = Client().get(f"/reviews/{query}")

    assert response.status_code == 200
    assert summary in response.content.decode()


@pytest.mark.django_db
def test_large_totals_use_a_thousands_separator_and_page_gaps() -> None:
    _seed(branches=1, per_branch=1801)

    content = Client().get("/reviews/?page=10").content.decode()

    assert "Showing 181-200 of 1,801 reviews" in content
    assert 'class="pager-gap"' in content
    assert 'href="?page=91"' in content


@pytest.mark.django_db
def test_review_text_is_escaped() -> None:
    _seed(branches=1, per_branch=1, text="<script>alert(1)</script>")

    content = Client().get("/reviews/").content.decode()

    assert "<script>alert(1)</script>" not in content
    assert "&lt;script&gt;" in content


@pytest.mark.django_db
def test_stars_have_a_tooltip_with_the_rating() -> None:
    _seed(branches=1, per_branch=1)

    assert 'title="1 out of 5"' in Client().get("/reviews/").content.decode()


@pytest.mark.django_db
def test_dates_are_shown_in_vietnam_time() -> None:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Airport")
    Review.objects.create(
        branch=branch, rating=5, text="ok", created_at=datetime(2026, 10, 14, 20, 0, tzinfo=UTC)
    )

    assert "Oct 15, 2026" in Client().get("/reviews/").content.decode()


@pytest.mark.django_db
def test_empty_reviews_page_shows_message() -> None:
    content = Client().get("/reviews/").content.decode()

    assert "No reviews yet" in content
    assert "Showing 0-0" not in content


@pytest.mark.django_db
def test_reviews_page_query_count_does_not_grow_with_branches(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    _seed(branches=20, per_branch=3)

    with django_assert_max_num_queries(3):
        response = Client().get("/reviews/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_menu_links_to_reviews_and_marks_it_active() -> None:
    _seed(branches=1, per_branch=1)

    dashboard = Client().get("/dashboard/").content.decode()
    reviews = Client().get("/reviews/").content.decode()

    assert 'href="/reviews/"' in dashboard
    assert 'href="/reviews/" aria-current="page"' in reviews


@pytest.mark.django_db
def test_export_button_is_not_shown_on_reviews_page() -> None:
    assert "Export JSON" in Client().get("/dashboard/").content.decode()
    assert "Export JSON" not in Client().get("/reviews/").content.decode()

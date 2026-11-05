from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review
from reviews.repositories import create_review

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


def _branch(name: str = "Riverside") -> Branch:
    business = Business.objects.get_or_create(name="Demo")[0]
    return Branch.objects.create(business=business, name=name)


def _reviews(branch: Branch, ratings: tuple[int, ...]) -> None:
    for index, rating in enumerate(ratings):
        create_review(
            branch=branch,
            rating=rating,
            text=f"Review number {index}",
            created_at=NOW - timedelta(days=index),
        )


@pytest.fixture
def riverside(db: None) -> Branch:
    branch = _branch()
    _reviews(branch, (5, 4, 3, 1, 1, 5, 5))
    return branch


def _html(branch_id: int | str) -> str:
    return Client().get(f"/locations/{branch_id}/").content.decode()


def test_page_has_title_heading_subtitle_and_no_export_button(riverside: Branch) -> None:
    response = Client().get(f"/locations/{riverside.pk}/")
    html = response.content.decode()

    assert response.status_code == 200
    assert "<title>Riverside · ReviewRadar</title>" in html
    assert "<h1>Riverside</h1>" in html
    assert "Score, weekly trend and latest reviews for this location." in html
    assert "Export JSON" not in html


def test_score_panel_shows_average_status_and_count(riverside: Branch) -> None:
    html = _html(riverside.pk)

    assert "Score" in html
    assert "3.4" in html
    assert "Watch" in html
    assert "7 reviews" in html


def test_one_review_is_singular(db: None) -> None:
    branch = _branch()
    _reviews(branch, (5,))

    html = _html(branch.pk)

    assert "1 review<" in html
    assert "Excellent" in html


def test_breakdown_lists_counts_and_percent_bars_without_links(riverside: Branch) -> None:
    html = _html(riverside.pk)

    assert "Rating breakdown" in html
    assert "width: 43%" in html  # 3 of 7 five-star reviews
    assert "width: 29%" in html  # 2 of 7 one-star reviews
    assert "/reviews/?rating=" not in html


def test_latest_reviews_are_five_newest_with_link_to_all(riverside: Branch) -> None:
    html = _html(riverside.pk)

    assert "Latest reviews" in html
    assert "Review number 0" in html and "Review number 4" in html
    assert "Review number 5" not in html
    assert html.index("Review number 0") < html.index("Review number 4")
    assert 'data-sensitive="review-text"' in html
    assert f'href="/reviews/?location={riverside.pk}"' in html
    assert "See all reviews" in html
    assert '<th scope="col">Location</th>' not in html


def test_same_time_reviews_show_higher_id_first(db: None) -> None:
    branch = _branch()
    for text in ("first", "second"):
        create_review(branch=branch, rating=4, text=text, created_at=NOW)

    html = _html(branch.pk)

    assert html.index("second") < html.index("first")


def test_location_without_reviews_shows_empty_states(db: None) -> None:
    branch = _branch("Newtown")

    html = _html(branch.pk)

    assert "No reviews yet" in html
    assert "0 reviews" in html
    assert "Reviews will appear here as soon as they are imported." in html
    assert "See all reviews" not in html
    assert "badge-" not in html.split('class="content"', 1)[1]


def test_reviews_of_other_locations_are_not_shown(riverside: Branch) -> None:
    other = _branch("Elsewhere")
    create_review(branch=other, rating=1, text="Other place text", created_at=NOW)

    assert "Other place text" not in _html(riverside.pk)


@pytest.mark.django_db
@pytest.mark.parametrize("pk", ["999999", "abc"])
def test_unknown_or_bad_id_answers_404(pk: str) -> None:
    response = Client().get(f"/locations/{pk}/")

    assert response.status_code == 404
    assert "Page not found" in response.content.decode()


@pytest.mark.login
@pytest.mark.django_db
def test_visitor_is_sent_to_sign_in() -> None:
    branch = _branch()

    response = Client().get(f"/locations/{branch.pk}/")

    assert response.status_code == 302
    assert response["Location"] == f"/login/?next=/locations/{branch.pk}/"


@pytest.mark.login
@pytest.mark.django_db
def test_signed_in_user_sees_the_page() -> None:
    branch = _branch()
    client = Client()
    client.force_login(get_user_model().objects.create_user(username="anna", password="x-y-z-123"))

    assert client.get(f"/locations/{branch.pk}/").status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("count", [5, 200])
def test_page_needs_at_most_four_queries(
    count: int, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    branch = _branch()
    Review.objects.bulk_create(
        Review(branch=branch, rating=4, text="x", created_at=NOW - timedelta(hours=i))
        for i in range(count)
    )

    with django_assert_max_num_queries(4):
        response = Client().get(f"/locations/{branch.pk}/")

    assert response.status_code == 200

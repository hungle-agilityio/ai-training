from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.models import Branch, Business, Review
from reviews.repositories import create_review


def _export(query: str = "") -> tuple[str, str, str]:
    response = Client().get(f"/reviews/export/{query}")
    assert response.status_code == 200
    body = b"".join(response.streaming_content).decode("utf-8")  # type: ignore[attr-defined]
    return body, response["Content-Type"], response["Content-Disposition"]


def _seed(count: int = 25) -> Branch:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")
    Review.objects.bulk_create(
        Review(
            branch=branch,
            rating=(index % 5) + 1,
            text=f"review {index}",
            created_at=datetime(2026, 10, 14, 2, 0, tzinfo=UTC).replace(minute=index),
        )
        for index in range(count)
    )
    return branch


@pytest.mark.django_db
def test_page_two_exports_every_matching_review_not_only_the_page() -> None:
    _seed(45)
    body, content_type, _ = _export("?page=2")

    assert content_type == "text/csv; charset=utf-8"
    assert len(body.splitlines()) == 46


@pytest.mark.django_db
def test_download_is_named_after_the_vietnam_date(mocker: MockerFixture) -> None:
    mocker.patch(
        "reviews.views.timezone.now", return_value=datetime(2026, 10, 21, 17, 30, tzinfo=UTC)
    )

    assert _export()[2] == 'attachment; filename="reviews-2026-10-22.csv"'


@pytest.mark.django_db
def test_export_follows_the_filters_of_the_page() -> None:
    branch = _seed(10)
    body, _, _ = _export(f"?location={branch.id}&rating=bad")

    ratings = [line.split(",")[1] for line in body.splitlines()[1:]]

    assert ratings == ["2", "1", "2", "1"]


@pytest.mark.django_db
def test_export_does_not_run_a_query_per_review(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    _seed(40)

    with django_assert_max_num_queries(3):
        _export()


@pytest.mark.django_db
def test_reviews_page_button_carries_the_filters_but_not_the_page() -> None:
    branch = _seed(45)
    html = Client().get(f"/reviews/?location={branch.id}&rating=good&page=2").content.decode()

    assert f'href="/reviews/export/?location={branch.id}&amp;rating=good"' in html
    assert "The file can contain customers' personal details." in html


@pytest.mark.django_db
def test_export_with_a_search_has_only_the_matching_reviews() -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")
    created_at = datetime(2026, 10, 14, 2, 0, tzinfo=UTC)
    create_review(branch=branch, rating=2, text="No parking nearby", created_at=created_at)
    create_review(branch=branch, rating=5, text="Great doctor", created_at=created_at)

    body, _, _ = _export("?search=PARKING")

    assert [line.split(",")[2] for line in body.splitlines()[1:]] == ["No parking nearby"]


@pytest.mark.django_db
def test_export_with_star_count_has_only_that_rating() -> None:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Airport")
    when = datetime(2026, 10, 14, 5, 0, tzinfo=UTC)
    for rating in (1, 3, 3, 5):
        Review.objects.create(branch=branch, rating=rating, text=f"r{rating}", created_at=when)

    body, _, _ = _export("?rating=3")

    ratings = [line.split(",")[1] for line in body.splitlines()[1:]]
    assert ratings == ["3", "3"]

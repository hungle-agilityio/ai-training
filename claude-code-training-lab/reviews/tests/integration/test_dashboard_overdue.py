import re
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews import services
from reviews.models import Branch, Business, Review, ReviewReply


def _review(branch: Branch, rating: int, age: timedelta, replied: bool = False) -> Review:
    created = timezone.now() - age
    review = Review.objects.create(branch=branch, rating=rating, text="t", created_at=created)
    if replied:
        ReviewReply.objects.create(review=review, text="r", created_at=created, updated_at=created)
    return review


@pytest.fixture
def branch() -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="B"), name="Airport")


def _card(html: str) -> str:
    match = re.search(r'<article class="kpi" id="kpi-needs-reply">.*?</article>', html, re.S)
    assert match
    return match.group(0)


@pytest.mark.django_db
def test_overdue_count_is_an_int_and_counts_old_unreplied_bad_reviews(branch: Branch) -> None:
    _review(branch, 1, timedelta(hours=30))
    _review(branch, 2, timedelta(days=4))
    _review(branch, 1, timedelta(days=4), replied=True)
    _review(branch, 1, timedelta(hours=5))
    _review(branch, 5, timedelta(days=4))

    count = services.dashboard_overview().overdue_count

    assert count == 2
    assert type(count) is int


@pytest.mark.django_db
def test_overdue_count_adds_up_over_locations(branch: Branch) -> None:
    other = Branch.objects.create(business=branch.business, name="Downtown")
    _review(branch, 1, timedelta(days=3))
    _review(other, 2, timedelta(days=3))

    assert services.dashboard_overview().overdue_count == 2


@pytest.mark.django_db
def test_a_bad_review_exactly_24_hours_old_is_not_overdue(branch: Branch) -> None:
    now = timezone.now()
    review = Review.objects.create(
        branch=branch, rating=1, text="t", created_at=now - timedelta(hours=24)
    )

    assert (
        services.dashboard_overview(now=review.created_at + timedelta(hours=24)).overdue_count == 0
    )
    one_second = review.created_at + timedelta(hours=24, seconds=1)
    assert services.dashboard_overview(now=one_second).overdue_count == 1


@pytest.mark.django_db
def test_card_links_to_overdue_list_when_some_are_overdue(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=3))

    card = _card(Client().get("/dashboard/").content.decode())

    assert (
        '<a class="row-link kpi-overdue" href="/replies/?overdue=1">1 overdue (bad, over 24 h)</a>'
        in card
    )
    assert card.index("overdue (bad") < card.index("Open reply drafts")


@pytest.mark.django_db
def test_card_says_none_overdue_without_a_link(branch: Branch) -> None:
    _review(branch, 1, timedelta(hours=2))

    card = _card(Client().get("/dashboard/").content.decode())

    assert "None overdue" in card
    assert "overdue=1" not in card


@pytest.mark.django_db
def test_demo_data_shows_one_overdue_review() -> None:
    call_command("seed_demo_data")

    card = _card(Client().get("/dashboard/").content.decode())

    assert "1 overdue (bad, over 24 h)" in card
    assert re.search(r'kpi-value">\s*5\s*<', card)


@pytest.mark.django_db
def test_dashboard_query_count_is_unchanged(
    branch: Branch, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    _review(branch, 1, timedelta(days=3))

    with django_assert_num_queries(3):
        assert Client().get("/dashboard/").status_code == 200


@pytest.mark.django_db
def test_api_dashboard_json_has_no_overdue_key(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=3))

    assert "overdue" not in Client().get("/api/dashboard/").content.decode()

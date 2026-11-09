import re
from datetime import UTC, datetime

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review
from reviews.repositories import create_review

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Demo"), name="Airport")


def _add(branch: Branch, rating: int, text: str) -> None:
    create_review(branch=branch, rating=rating, text=text, created_at=NOW)


def _html(branch: Branch) -> str:
    return Client().get(f"/locations/{branch.pk}/").content.decode()


def _panel(html: str) -> str:
    start = html.index('id="location-topics"')
    return html[start : html.index("</section>", start)]


def _seed(branch: Branch) -> None:
    _add(branch, 1, "long wait")
    _add(branch, 2, "slow queue")
    _add(branch, 5, "wait but great")
    _add(branch, 1, "parking was full")
    _add(branch, 5, "friendly staff")
    _add(branch, 4, "clean room")


def test_panel_sits_between_trend_and_latest_reviews(branch: Branch) -> None:
    _seed(branch)
    html = _html(branch)
    assert html.index("Weekly trend") < html.index('id="location-topics"')
    assert html.index('id="location-topics"') < html.index("Latest reviews")
    assert '<section class="panel" id="location-topics">' in html
    panel = _panel(html)
    assert "What customers talk about" in panel
    assert "Top topics of all reviews" in panel


def test_panel_lists_top_three_with_links_counts_and_bad(branch: Branch) -> None:
    _seed(branch)
    panel = _panel(_html(branch))
    assert f'href="/reviews/?location={branch.pk}&amp;topic=wait"' in panel
    assert "Wait time" in panel
    assert "3 reviews · 2 bad" in panel
    assert panel.count("<li") == 3
    assert "1 review</span>" in panel
    assert "1 reviews" not in panel
    order = [panel.index(label) for label in ("Wait time", "Cleanliness", "Parking")]
    assert order == sorted(order)
    assert "Staff" not in panel


def test_panel_hides_bad_when_zero(branch: Branch) -> None:
    _add(branch, 5, "friendly staff")
    panel = _panel(_html(branch))
    assert "1 review" in panel
    assert " bad" not in panel


def test_panel_without_topics_says_no_topics_yet(branch: Branch) -> None:
    _add(branch, 5, "fine")
    panel = _panel(_html(branch))
    assert "No topics yet" in panel
    assert "<li" not in panel


def test_location_without_reviews_says_no_topics_yet_and_no_badge(branch: Branch) -> None:
    html = _html(branch)
    assert "No topics yet" in _panel(html)
    assert "badge-" not in html.split('class="content"', 1)[1]


DEMO_TOPICS = [
    ("Airport", ["Wait time 3 reviews · 2 bad", "Booking & phone 1 review · 1 bad"]),
    ("Downtown", ["Staff 2 reviews", "Cleanliness 1 review"]),
    ("Riverside", ["Doctor & treatment 2 reviews", "Booking & phone 1 review · 1 bad"]),
]


@pytest.mark.parametrize(("name", "expected"), DEMO_TOPICS)
def test_demo_locations_show_expected_topics(db: None, name: str, expected: list[str]) -> None:
    call_command("seed_demo_data")
    panel = _panel(_html(Branch.objects.get(name=name)))
    rows = [
        " ".join(re.sub(r"<[^>]+>", " ", item).replace("&amp;", "&").split())
        for item in panel.split("<li>")[1:]
    ]
    assert rows[: len(expected)] == expected
    assert len(rows) == 3


def test_page_needs_at_most_five_queries(
    branch: Branch, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    Review.objects.bulk_create(
        Review(branch=branch, rating=4, text="long wait", created_at=NOW) for _ in range(200)
    )
    with django_assert_max_num_queries(5):
        response = Client().get(f"/locations/{branch.pk}/")
    assert response.status_code == 200

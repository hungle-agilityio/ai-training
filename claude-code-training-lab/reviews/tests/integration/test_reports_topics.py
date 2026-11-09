from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.models import Branch, Business
from reviews.report_service import monthly_report
from reviews.repositories import create_review

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fixed_now(mocker: MockerFixture) -> None:
    mocker.patch("reviews.views.timezone.now", return_value=NOW)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")


def _add(branch: Branch, rating: int, text: str, month: int, day: int, hour: int = 5) -> None:
    created = datetime(2026, month, day, hour, 0, tzinfo=UTC)
    create_review(branch=branch, rating=rating, text=text, created_at=created)


def _html(query: str = "") -> str:
    return Client().get(f"/reports/{query}").content.decode()


def _panel(html: str) -> str:
    return html[html.index('id="report-topics"') :]


def _seed(branch: Branch) -> None:
    _add(branch, 1, "slow", 11, 3)
    _add(branch, 5, "slow", 11, 4)
    _add(branch, 5, "slow staff", 10, 4)
    _add(branch, 5, "clean", 10, 5)
    _add(branch, 4, "slow", 9, 5)


def test_panel_follows_locations_panel(branch: Branch) -> None:
    _seed(branch)
    html = _html()
    assert html.index("<h2>Locations</h2>") < html.index('id="report-topics"')
    panel = _panel(html)
    assert "<h2>Topics</h2>" in panel
    assert "Reviews per topic in November 2026" in panel


def test_table_columns_and_order(branch: Branch) -> None:
    _seed(branch)
    panel = _panel(_html())
    assert 'class="table-wrap"' in panel
    for header in ("Topic", "Reviews", "Bad", "Change vs October"):
        assert header in panel
    assert panel.index("Wait time") < panel.index("Cleanliness")
    assert "Staff" in panel


def test_change_markup(branch: Branch) -> None:
    _seed(branch)
    panel = _panel(_html())
    assert '<span class="change-up" aria-label="Up 1 from October">▲ 1</span>' in panel
    assert '<span class="change-down" aria-label="Down 1 from October">▼ 1</span>' in panel


def test_same_change_markup(branch: Branch) -> None:
    _add(branch, 5, "clean", 11, 3)
    _add(branch, 5, "clean", 10, 3)
    panel = _panel(_html())
    assert '<span class="change-same" aria-label="Same as October">0</span>' in panel


def test_empty_month_shows_message_without_table(branch: Branch) -> None:
    _add(branch, 5, "fine", 11, 3)
    panel = _panel(_html())
    assert "No topics this month." in panel
    assert "<table" not in panel


def test_vietnam_time_edges(branch: Branch) -> None:
    _add(branch, 5, "slow", 10, 31, 17)  # 00:00 on 1 November in Vietnam
    _add(branch, 5, "slow", 10, 31, 16)  # still October in Vietnam
    topics = monthly_report(None, NOW).topics
    assert [(t.label, t.review_count, t.change) for t in topics] == [("Wait time", 1, 0)]


def test_chosen_month_uses_its_previous_month(branch: Branch) -> None:
    _seed(branch)
    panel = _panel(_html("?month=2026-10"))
    assert "Reviews per topic in October 2026" in panel
    assert "Change vs September" in panel


def test_page_makes_at_most_two_queries(
    branch: Branch, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    _seed(branch)
    with django_assert_max_num_queries(2):
        Client().get("/reports/")


def test_export_makes_at_most_two_queries(
    branch: Branch, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    _seed(branch)
    with django_assert_max_num_queries(2):
        Client().get("/reports/export/")

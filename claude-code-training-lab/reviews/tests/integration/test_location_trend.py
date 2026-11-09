import re
from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.models import Branch, Business, Review

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
PANEL_LINE = "Average rating per week, last 8 weeks (Monday to Sunday)"


@pytest.fixture(autouse=True)
def fixed_now(mocker: MockerFixture) -> None:
    mocker.patch("reviews.views.timezone.now", return_value=NOW)


def _branch(name: str = "Riverside") -> Branch:
    business = Business.objects.get_or_create(name="Demo")[0]
    return Branch.objects.create(business=business, name=name)


def _review(branch: Branch, rating: int, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text="ok", created_at=created_at)


@pytest.fixture
def riverside(db: None) -> Branch:
    branch = _branch()
    # Week of Oct 26: 4, 3, 3, 3 -> 3.25 -> 3.3 (half up)
    for day, rating in ((26, 4), (27, 3), (28, 3), (30, 3)):
        _review(branch, rating, datetime(2026, 10, day, 5, 0, tzinfo=UTC))
    # Week of Nov 2: one review rated 4
    _review(branch, 4, datetime(2026, 11, 2, 1, 0, tzinfo=UTC))
    return branch


def _html(branch: Branch) -> str:
    return Client().get(f"/locations/{branch.pk}/").content.decode()


def _trend_panel(html: str) -> str:
    start = html.index("Weekly trend")
    return html[start : html.index("Latest reviews")]


def test_trend_panel_sits_between_breakdown_and_latest_reviews(riverside: Branch) -> None:
    html = _html(riverside)

    assert PANEL_LINE in html
    breakdown = html.index("Rating breakdown")
    assert breakdown < html.index("Weekly trend") < html.index("Latest reviews")


def test_chart_has_eight_columns_oldest_first_with_bars_and_dashes(riverside: Branch) -> None:
    panel = _trend_panel(_html(riverside))

    columns = re.findall(r'<li class="trend-col[^"]*"[^>]*>(.*?)</li>', panel, re.S)
    assert len(columns) == 8
    assert "–" in columns[0]
    assert "trend-bar" not in columns[0]
    assert "3.3" in columns[6]
    assert 'style="height: 66%"' in columns[6]
    assert "4.0" in columns[7]
    assert 'style="height: 80%"' in columns[7]
    assert "Oct 26" in columns[6]
    assert "4 reviews" in columns[6]
    assert "1 review<" in columns[7].replace("</span>", "<")


def test_bars_are_hidden_from_screen_readers(riverside: Branch) -> None:
    panel = _trend_panel(_html(riverside))

    assert 'class="trend-chart" aria-hidden="true"' in panel


def test_table_lists_eight_weeks_with_no_reviews_text(riverside: Branch) -> None:
    panel = _trend_panel(_html(riverside))

    for header in ("Week of", "Average", "Reviews"):
        assert f">{header}</th>" in panel
    rows = re.findall(r"<tr>\s*<th scope=\"row\">.*?</tr>", panel, re.S)
    assert len(rows) == 8
    assert rows[0].count("No reviews") == 1
    assert "No reviews" not in rows[6]
    assert "3.3" in rows[6]
    assert "Oct 26" in rows[6]


def test_location_without_reviews_shows_eight_empty_weeks(db: None) -> None:
    branch = _branch("Newtown")

    panel = _trend_panel(_html(branch))

    assert panel.count("No reviews") == 8
    assert "trend-bar" not in panel


def test_chart_uses_no_script_image_or_external_file(riverside: Branch) -> None:
    panel = _trend_panel(_html(riverside))

    assert "<script" not in panel
    assert "<img" not in panel
    assert "http" not in panel


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

    with django_assert_max_num_queries(5):
        response = Client().get(f"/locations/{branch.pk}/")

    assert response.status_code == 200

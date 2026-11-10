import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review


def _branch(name: str, goal: str | None, ratings: tuple[int, ...] = ()) -> Branch:
    business, _ = Business.objects.get_or_create(name="Demo")
    branch = Branch.objects.create(
        business=business, name=name, target_score=Decimal(goal) if goal else None
    )
    for rating in ratings:
        Review.objects.create(
            branch=branch,
            rating=rating,
            text="t",
            created_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
    return branch


def _scores_html() -> str:
    html = Client().get("/dashboard/").content.decode()
    match = re.search(r'id="location-scores".*?</section>', html, re.DOTALL)
    assert match
    return re.sub(r"\s+", " ", match.group(0))


def _cells(html: str, name: str) -> list[str]:
    row = re.search(rf"<tr>\s*<th scope=\"row\">.*?{name}.*?</tr>", html)
    assert row
    return re.findall(r"<td[^>]*>(.*?)</td>", row.group(0))


@pytest.mark.django_db
def test_goal_header_sits_right_after_rating_before_status() -> None:
    _branch("Downtown", "4.5", (4, 4))

    html = _scores_html()

    headers = re.findall(r'<th scope="col"[^>]*>(.*?)</th>', html)
    assert headers == [
        "Location",
        "Reviews",
        "Rating",
        "Goal",
        "Status",
        "Replied in 24h",
        "Details",
    ]


@pytest.mark.django_db
def test_short_location_shows_goal_and_gap_with_watch_badge() -> None:
    _branch("Downtown", "4.5", (4, 4))

    cell = _cells(_scores_html(), "Downtown")[2]

    assert "4.5" in cell
    assert "&middot;" in cell or "·" in cell
    assert '<span class="badge badge-watch">0.5 short</span>' in cell


@pytest.mark.django_db
def test_met_location_uses_positive_badge() -> None:
    _branch("Riverside", "3.0", (4, 4))

    cell = _cells(_scores_html(), "Riverside")[2]

    assert "3.0" in cell
    assert '<span class="badge badge-positive">Met</span>' in cell


@pytest.mark.django_db
def test_goal_with_no_reviews_says_no_score_yet() -> None:
    _branch("Newcomer", "4.0")

    cell = _cells(_scores_html(), "Newcomer")[2]

    assert "4.0" in cell
    assert "No score yet" in cell
    assert "badge" not in cell


@pytest.mark.django_db
def test_location_without_goal_shows_only_a_muted_dash() -> None:
    _branch("Airport", None, (5,))

    cell = _cells(_scores_html(), "Airport")[2].strip()

    assert cell == '<span class="muted">&ndash;</span>'


@pytest.mark.django_db
@pytest.mark.parametrize("branch_count", [3, 30])
def test_dashboard_with_goals_still_runs_three_queries(
    branch_count: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    for index in range(branch_count):
        _branch(f"Branch {index}", "4.0", (3, 5))

    with django_assert_num_queries(3):
        response = Client().get("/dashboard/")

    assert response.status_code == 200

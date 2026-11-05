from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.models import Branch, Business, Review
from reviews.report_service import monthly_report

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)
JAN = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fixed_now(mocker: MockerFixture) -> None:
    mocker.patch("reviews.views.timezone.now", return_value=NOW)


def _branch(name: str) -> Branch:
    business = Business.objects.get_or_create(name="Demo")[0]
    return Branch.objects.create(business=business, name=name)


def _reviews(branch: Branch, year: int, month: int, ratings: list[int]) -> None:
    Review.objects.bulk_create(
        Review(
            branch=branch,
            rating=rating,
            text="ok",
            created_at=datetime(year, month, 10 + i, 5, 0, tzinfo=UTC),
        )
        for i, rating in enumerate(ratings)
    )


def _change(name: str, now: datetime = NOW) -> float | None:
    rows = {row.name: row for row in monthly_report(None, now).rows}
    return rows[name].change


@pytest.mark.django_db
def test_change_is_rounded_difference_of_displayed_averages() -> None:
    a, b = _branch("A"), _branch("B")
    _reviews(a, 2026, 11, [3, 4, 4, 4, 3, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 4, 3, 4, 3, 3])
    _reviews(b, 2026, 10, [3, 3, 3, 3, 3, 3, 3, 3, 3, 4])
    _reviews(a, 2026, 10, [3, 3, 3, 3, 3, 3, 3, 3, 3, 4])
    _reviews(b, 2026, 11, [4])
    change = _change("A")
    assert change == 0.4  # 3.5 - 3.1, never 0.3999999999999999
    assert isinstance(change, float)
    assert _change("B") == 0.9


@pytest.mark.django_db
def test_change_is_exactly_zero_point_three() -> None:
    a = _branch("A")
    _reviews(a, 2026, 11, [3, 4, 4, 3, 3, 4, 4, 3, 3, 4])  # 3.5
    _reviews(a, 2026, 10, [3, 3, 3, 3, 3, 3, 4, 3, 3, 4])  # 3.2
    assert _change("A") == 0.3


@pytest.mark.django_db
def test_change_is_none_when_either_month_has_no_reviews() -> None:
    _reviews(_branch("OnlyNow"), 2026, 11, [4])
    _reviews(_branch("OnlyBefore"), 2026, 10, [4])
    _branch("Neither")
    assert _change("OnlyNow") is None
    assert _change("OnlyBefore") is None
    assert _change("Neither") is None


@pytest.mark.django_db
def test_previous_month_of_january_is_december_of_the_year_before() -> None:
    branch = _branch("A")
    _reviews(branch, 2026, 1, [5])
    _reviews(branch, 2025, 12, [3])
    assert _change("A", JAN) == 2.0
    assert monthly_report(None, JAN).previous_label == "December"


@pytest.mark.django_db
def test_column_shows_up_down_same_and_no_comparison() -> None:
    up, down, same, none = _branch("Up"), _branch("Down"), _branch("Same"), _branch("None")
    _reviews(up, 2026, 11, [4])
    _reviews(up, 2026, 10, [3])
    _reviews(down, 2026, 11, [2])
    _reviews(down, 2026, 10, [4])
    _reviews(same, 2026, 11, [3])
    _reviews(same, 2026, 10, [3])
    _reviews(none, 2026, 11, [3])
    html = Client().get("/reports/").content.decode()
    assert '<th scope="col">vs October</th>' in html
    assert 'class="change-up" aria-label="Up 1.0 from October">▲ 1.0<' in html
    assert 'class="change-down" aria-label="Down 2.0 from October">▼ 2.0<' in html
    assert 'class="change-same" aria-label="Same as October">0.0<' in html
    assert 'aria-label="No comparison">—<' in html


@pytest.mark.django_db
def test_july_has_no_comparison_in_any_row() -> None:
    _reviews(_branch("A"), 2026, 7, [4])
    html = Client().get("/reports/?month=2026-07").content.decode()
    assert "vs June" in html
    assert html.count('aria-label="No comparison"') == 1


def test_change_classes_are_styled_in_app_css() -> None:
    css = (Path(__file__).parents[2] / "static/reviews/app.css").read_text(encoding="utf-8")
    for name in ("change-up", "change-down", "change-same"):
        assert f".{name}" in css


@pytest.mark.django_db
@pytest.mark.parametrize(("branch_count", "review_count"), [(3, 6), (30, 300)])
def test_page_makes_at_most_two_queries(
    branch_count: int, review_count: int, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    branches = [_branch(f"Branch {i:02d}") for i in range(branch_count)]
    for index in range(review_count):
        month = 11 if index % 2 else 10
        _reviews(branches[index % branch_count], 2026, month, [1 + index % 5])
    with django_assert_max_num_queries(2):
        response = Client().get("/reports/")
    assert response.status_code == 200

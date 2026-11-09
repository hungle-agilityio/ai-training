from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture

from reviews import compare_service
from reviews.compare_repository import CompareTotals

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


def totals(
    branch_id: int,
    stars: tuple[int, int, int, int, int],
    bad_counted: int = 0,
    in_time: int = 0,
) -> CompareTotals:
    count = sum(stars)
    total = sum(star * n for star, n in zip((5, 4, 3, 2, 1), stars, strict=True))
    return CompareTotals(branch_id, f"L{branch_id}", count, total, stars, bad_counted, in_time)


def patch(mocker: MockerFixture, *rows: CompareTotals) -> None:
    mocker.patch(
        "reviews.compare_service.compare_repository.compare_totals", return_value=list(rows)
    )


def test_side_numbers_follow_the_shared_rules(mocker: MockerFixture) -> None:
    patch(mocker, totals(1, (2, 1, 2, 0, 0)), totals(2, (1, 2, 0, 2, 0), 2, 1))

    result = compare_service.compare_locations(1, 2, None, NOW)

    assert result is not None
    assert result.a.average_rating == 4.0
    assert isinstance(result.a.average_rating, float)
    assert (result.a.good_percent, result.a.bad_percent) == (60, 0)
    assert result.a.replied_in_time_percent is None
    assert result.b.average_rating == 3.4
    assert result.b.bad_percent == 40
    assert result.b.replied_in_time_percent == 50
    assert isinstance(result.b.replied_in_time_percent, int)
    assert [(r.stars, r.count, r.percent) for r in result.a.star_rows] == [
        (5, 2, 40),
        (4, 1, 20),
        (3, 2, 40),
        (2, 0, 0),
        (1, 0, 0),
    ]
    assert result.period_label == "All time"


def test_difference_is_a_minus_b_with_one_decimal(mocker: MockerFixture) -> None:
    patch(mocker, totals(1, (2, 1, 2, 0, 0)), totals(2, (1, 2, 0, 2, 0)))

    result = compare_service.compare_locations(1, 2, None, NOW)

    assert result is not None
    assert result.difference == 0.6
    assert isinstance(result.difference, float)


def test_no_reviews_gives_no_score_no_shares_and_no_difference(mocker: MockerFixture) -> None:
    patch(mocker, totals(1, (0, 0, 0, 0, 0)), totals(2, (1, 0, 0, 0, 0)))

    result = compare_service.compare_locations(1, 2, 30, NOW)

    assert result is not None
    assert result.a.average_rating is None
    assert result.a.good_percent is None
    assert result.a.bad_percent is None
    assert all(r.percent == 0 for r in result.a.star_rows)
    assert result.difference is None
    assert result.period_label == "Last 30 days"


def test_same_location_twice_is_not_a_comparison(mocker: MockerFixture) -> None:
    fetch = mocker.patch("reviews.compare_service.compare_repository.compare_totals")

    assert compare_service.compare_locations(1, 1, None, NOW) is None
    fetch.assert_not_called()


def test_unknown_location_is_not_a_comparison(mocker: MockerFixture) -> None:
    patch(mocker, totals(1, (1, 0, 0, 0, 0)))

    assert compare_service.compare_locations(1, 99, None, NOW) is None


@pytest.mark.parametrize(
    ("days", "label"), [(None, "All time"), (30, "Last 30 days"), (90, "Last 90 days")]
)
def test_period_labels(mocker: MockerFixture, days: int | None, label: str) -> None:
    patch(mocker, totals(1, (1, 0, 0, 0, 0)), totals(2, (1, 0, 0, 0, 0)))

    result = compare_service.compare_locations(1, 2, days, NOW)

    assert result is not None
    assert result.period_label == label

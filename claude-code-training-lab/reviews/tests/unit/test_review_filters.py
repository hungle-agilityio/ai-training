from datetime import UTC, date, datetime

import pytest
from django.utils import timezone

from reviews.forms import ReviewFilterForm
from reviews.models import Branch, Business, Review
from reviews.repositories import branch_choices
from reviews.services import (
    ReviewFilters,
    reviews_page,
    week_containing,
    week_label,
)

# Week 42 of 2026 runs Monday 12 Oct to Sunday 18 Oct, Vietnam time (UTC+7)
WEEK_DAY = date(2026, 10, 14)


def _utc(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0
) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def _add(branch: Branch, rating: int, text: str, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text=text, created_at=created_at)


def _branches() -> tuple[Branch, Branch]:
    business = Business.objects.create(name="Demo")
    return (
        Branch.objects.create(business=business, name="Airport"),
        Branch.objects.create(business=business, name="Downtown"),
    )


def _texts(filters: ReviewFilters, per_page: int = 100) -> list[str]:
    return [row.text for row in reviews_page(None, per_page, filters).rows]


# --- week -------------------------------------------------------------------------------------


@pytest.mark.parametrize("day", [date(2026, 10, 12), date(2026, 10, 14), date(2026, 10, 18)])
def test_any_day_gives_the_monday_to_sunday_week_in_vietnam_time(day: date) -> None:
    week = week_containing(day)

    assert week.start == _utc(2026, 10, 11, 17, 0)  # Monday 12 Oct 00:00 in Vietnam
    assert week.end == _utc(2026, 10, 18, 17, 0)  # Monday 19 Oct 00:00 in Vietnam
    assert week.start.tzinfo is not None
    assert week.label == "Oct 12 - Oct 18, 2026"


@pytest.mark.parametrize(
    ("monday", "label"),
    [
        (date(2026, 10, 12), "Oct 12 - Oct 18, 2026"),
        (date(2026, 9, 28), "Sep 28 - Oct 4, 2026"),
        (date(2026, 12, 28), "Dec 28, 2026 - Jan 3, 2027"),  # ISO week 53 of 2026
    ],
)
def test_week_label(monday: date, label: str) -> None:
    assert week_label(monday) == label


def test_week_across_the_new_year_is_seven_days() -> None:
    week = week_containing(date(2027, 1, 1))

    assert week.label == "Dec 28, 2026 - Jan 3, 2027"
    assert (week.end - week.start).days == 7


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("created_at", "in_week"),
    [
        (_utc(2026, 10, 11, 16, 59, 59), False),  # Sunday 23:59:59 in Vietnam, the week before
        (_utc(2026, 10, 11, 17, 0), True),  # Monday 00:00 in Vietnam, first moment
        (_utc(2026, 10, 18, 16, 59, 59), True),  # Sunday 23:59:59 in Vietnam, last moment
        (_utc(2026, 10, 18, 17, 0), False),  # next Monday 00:00 in Vietnam
        (_utc(2026, 10, 18, 17, 30), False),  # Sunday 17:30 UTC is Monday 00:30 next week
    ],
)
def test_week_boundaries_follow_vietnam_time(created_at: datetime, in_week: bool) -> None:
    airport, _ = _branches()
    _add(airport, 4, "edge", created_at)

    assert (_texts(ReviewFilters(day=WEEK_DAY)) == ["edge"]) is in_week


@pytest.mark.django_db
def test_week_filter_does_not_depend_on_the_active_time_zone() -> None:
    airport, _ = _branches()
    _add(airport, 4, "edge", _utc(2026, 10, 18, 17, 30))
    _add(airport, 4, "inside", _utc(2026, 10, 14, 5, 0))

    with timezone.override("America/Chicago"):
        assert _texts(ReviewFilters(day=WEEK_DAY)) == ["inside"]
        assert _texts(ReviewFilters(day=date(2026, 10, 19))) == ["edge"]


# --- location, rating, combined -------------------------------------------------------------


@pytest.fixture
def seeded() -> tuple[Branch, Branch]:
    airport, downtown = _branches()
    in_week = _utc(2026, 10, 14, 5, 0)
    for rating in (1, 2, 3, 4, 5):
        _add(airport, rating, f"airport-{rating}", in_week)
    _add(downtown, 1, "downtown-1", in_week)
    _add(downtown, 5, "downtown-5", in_week)
    _add(airport, 1, "airport-old", _utc(2026, 10, 5, 5, 0))
    return airport, downtown


@pytest.mark.django_db
def test_no_filter_lists_every_review_including_three_stars(seeded: tuple[Branch, Branch]) -> None:
    page = reviews_page(None)

    assert page.total == 8
    assert "airport-3" in _texts(ReviewFilters())
    assert page.is_filtered is False


@pytest.mark.django_db
def test_location_filter_keeps_only_that_location(seeded: tuple[Branch, Branch]) -> None:
    _, downtown = seeded

    page = reviews_page(None, filters=ReviewFilters(branch_id=downtown.id))

    assert {row.branch_name for row in page.rows} == {"Downtown"}
    assert page.total == 2


@pytest.mark.django_db
@pytest.mark.parametrize(("rating", "expected"), [("good", {4, 5}), ("bad", {1, 2})])
def test_good_and_bad_keep_only_their_stars(
    seeded: tuple[Branch, Branch], rating: str, expected: set[int]
) -> None:
    page = reviews_page(None, filters=ReviewFilters(rating=rating))

    assert {row.rating for row in page.rows} == expected
    assert 3 not in {row.rating for row in page.rows}


@pytest.mark.django_db
def test_filters_combine(seeded: tuple[Branch, Branch]) -> None:
    airport, _ = seeded

    texts = _texts(ReviewFilters(branch_id=airport.id, rating="bad", day=WEEK_DAY))

    assert sorted(texts) == ["airport-1", "airport-2"]


@pytest.mark.django_db
def test_unknown_location_is_ignored(seeded: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, filters=ReviewFilters(branch_id=9999))

    assert page.total == 8
    assert page.is_filtered is False
    assert page.query_params == []


@pytest.mark.django_db
def test_summary_counts_only_matches(seeded: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, filters=ReviewFilters(rating="bad", day=WEEK_DAY))

    assert (page.start_index, page.end_index, page.total) == (1, 3, 3)
    assert page.week_label == "Oct 12 - Oct 18, 2026"
    assert page.week_value == "2026-10-14"


@pytest.mark.django_db
def test_page_links_keep_the_applied_filters() -> None:
    airport, _ = _branches()
    for index in range(25):
        _add(airport, 1, f"bad-{index}", _utc(2026, 10, 14, 5, index))

    page = reviews_page(1, filters=ReviewFilters(branch_id=airport.id, rating="bad", day=WEEK_DAY))

    assert page.next_href == f"?location={airport.id}&rating=bad&week=2026-10-14&page=2"
    assert page.links[1].href.endswith("&page=2")
    assert reviews_page(1).next_href == "?page=2"


@pytest.mark.django_db
def test_page_beyond_the_end_of_a_filtered_list_falls_back_to_last(
    seeded: tuple[Branch, Branch],
) -> None:
    page = reviews_page(9999, 2, ReviewFilters(rating="bad"))

    assert (page.number, page.num_pages) == (2, 2)


@pytest.mark.django_db
def test_dropdown_lists_every_location_by_name_and_marks_the_chosen_one() -> None:
    business = Business.objects.create(name="Demo")
    newtown = Branch.objects.create(business=business, name="Newtown")
    Branch.objects.create(business=business, name="Airport")

    page = reviews_page(None, filters=ReviewFilters(branch_id=newtown.id))

    assert [(option.name, option.is_selected) for option in page.branches] == [
        ("Airport", False),
        ("Newtown", True),
    ]
    assert page.total == 0
    assert page.is_filtered is True
    assert [name for _, name in branch_choices()] == ["Airport", "Newtown"]


# --- form -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("location", "abc"),
        ("location", "0"),
        ("location", "-1"),
        ("rating", "meh"),
        ("rating", "GOOD"),
        ("week", "2026-13-01"),
        ("week", "2026-W42"),
        ("week", "14/10/2026"),
        ("week", "9999-12-31"),
        ("week", "1999-12-31"),
    ],
)
def test_form_ignores_a_wrong_value_but_keeps_the_others(field: str, value: str) -> None:
    data = {"location": "3", "rating": "bad", "week": "2026-10-14", field: value}

    filters = ReviewFilterForm(data).filters()

    expected = ReviewFilters(branch_id=3, rating="bad", day=date(2026, 10, 14))
    wrong = {"location": "branch_id", "rating": "rating", "week": "day"}[field]
    assert filters == ReviewFilters(**{**expected.__dict__, wrong: None})


def test_form_reads_valid_values_and_empty_means_not_chosen() -> None:
    assert ReviewFilterForm(
        {"location": "2", "rating": "good", "week": "2026-10-14"}
    ).filters() == (ReviewFilters(branch_id=2, rating="good", day=date(2026, 10, 14)))
    assert ReviewFilterForm({"location": "", "rating": "", "week": ""}).filters() == ReviewFilters()
    assert ReviewFilterForm({}).filters() == ReviewFilters()

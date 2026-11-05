from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from reviews.models import Branch, Business, Review
from reviews.report_service import REPORT_MONTHS, MonthOption, monthly_report

VN = ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=VN)


@pytest.fixture
def business() -> Business:
    return Business.objects.create(name="Demo")


def _add(branch: Branch, rating: int, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text="ok", created_at=created_at)


@pytest.mark.django_db
def test_options_are_twelve_months_newest_first() -> None:
    report = monthly_report(None, NOW)

    assert REPORT_MONTHS == 12
    assert len(report.options) == 12
    assert report.options[0] == MonthOption(value="2026-11", label="November 2026")
    assert report.options[1] == MonthOption(value="2026-10", label="October 2026")
    assert report.options[-1] == MonthOption(value="2025-12", label="December 2025")


@pytest.mark.django_db
def test_default_month_is_the_current_month() -> None:
    report = monthly_report(None, NOW)

    assert report.month == date(2026, 11, 1)
    assert report.label == "November 2026"


@pytest.mark.django_db
def test_chosen_month_in_the_options_is_used() -> None:
    report = monthly_report(date(2026, 9, 1), NOW)

    assert report.month == date(2026, 9, 1)
    assert report.label == "September 2026"


@pytest.mark.django_db
@pytest.mark.parametrize("chosen", [date(2024, 1, 1), date(2025, 11, 1), date(2027, 1, 1)])
def test_month_outside_the_options_falls_back_to_current(chosen: date) -> None:
    assert monthly_report(chosen, NOW).month == date(2026, 11, 1)


@pytest.mark.django_db
def test_month_not_first_day_falls_back_to_current() -> None:
    assert monthly_report(date(2026, 10, 15), NOW).month == date(2026, 11, 1)


@pytest.mark.django_db
def test_current_month_follows_vietnam_time_not_utc() -> None:
    # 31 Oct 20:00 UTC is already 1 Nov 03:00 in Vietnam
    report = monthly_report(None, datetime(2026, 10, 31, 20, 0, tzinfo=UTC))

    assert report.month == date(2026, 11, 1)


@pytest.mark.django_db
def test_month_edge_uses_vietnam_time(business: Business) -> None:
    branch = Branch.objects.create(business=business, name="Riverside")
    _add(branch, 5, datetime(2026, 10, 31, 23, 59, tzinfo=VN))
    _add(branch, 1, datetime(2026, 11, 1, 0, 0, tzinfo=VN))

    october = monthly_report(date(2026, 10, 1), NOW).rows[0]
    november = monthly_report(date(2026, 11, 1), NOW).rows[0]

    assert (october.review_count, october.average_rating) == (1, 5.0)
    assert (november.review_count, november.average_rating) == (1, 1.0)


@pytest.mark.django_db
def test_other_active_time_zone_does_not_move_the_month(business: Business) -> None:
    branch = Branch.objects.create(business=business, name="Riverside")
    _add(branch, 4, datetime(2026, 10, 31, 23, 59, tzinfo=VN))

    with timezone.override(ZoneInfo("America/Los_Angeles")):
        row = monthly_report(date(2026, 10, 1), NOW).rows[0]

    assert row.review_count == 1


@pytest.mark.django_db
def test_row_numbers_average_half_up_and_good_bad_bands(business: Business) -> None:
    branch = Branch.objects.create(business=business, name="Riverside")
    for rating in (5, 2, 4, 2, 3):
        _add(branch, rating, datetime(2026, 11, 2, 10, 0, tzinfo=VN))
    # outside the month
    _add(branch, 1, datetime(2026, 10, 2, 10, 0, tzinfo=VN))

    row = monthly_report(None, NOW).rows[0]

    assert row.branch_id == branch.id
    assert row.name == "Riverside"
    assert row.review_count == 5
    assert row.average_rating == 3.2
    assert isinstance(row.average_rating, float)
    assert row.good_count == 2
    assert row.bad_count == 2


@pytest.mark.django_db
def test_average_of_5_2_4_2_is_3_3(business: Business) -> None:
    branch = Branch.objects.create(business=business, name="Riverside")
    for rating in (5, 2, 4, 2):
        _add(branch, rating, datetime(2026, 11, 2, 10, 0, tzinfo=VN))

    assert monthly_report(None, NOW).rows[0].average_rating == 3.3


@pytest.mark.django_db
def test_location_without_reviews_keeps_a_row_with_no_score(business: Business) -> None:
    Branch.objects.create(business=business, name="Quiet")

    row = monthly_report(None, NOW).rows[0]

    assert row.average_rating is None
    assert (row.review_count, row.good_count, row.bad_count) == (0, 0, 0)


@pytest.mark.django_db
def test_rows_ordered_by_name_then_id(business: Business) -> None:
    zed = Branch.objects.create(business=business, name="Zed")
    same_a = Branch.objects.create(business=business, name="Airport")
    same_b = Branch.objects.create(business=business, name="Airport")

    rows = monthly_report(None, NOW).rows

    assert [r.branch_id for r in rows] == [same_a.id, same_b.id, zed.id]

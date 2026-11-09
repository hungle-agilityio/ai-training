from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.forms import ReportMonthForm
from reviews.models import Branch, Business, Review

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fixed_now(mocker: MockerFixture) -> None:
    mocker.patch("reviews.views.timezone.now", return_value=NOW)


def _branch(name: str) -> Branch:
    business = Business.objects.get_or_create(name="Demo")[0]
    return Branch.objects.create(business=business, name=name)


def _review(branch: Branch, rating: int, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text="ok", created_at=created_at)


@pytest.fixture
def riverside(db: None) -> Branch:
    branch = _branch("Riverside")
    for day, rating in ((2, 4), (3, 3), (4, 3)):
        _review(branch, rating, datetime(2026, 11, day, 5, 0, tzinfo=UTC))
    _review(branch, 1, datetime(2026, 7, 10, 5, 0, tzinfo=UTC))
    _branch("Airport")
    return branch


def _html(query: str = "") -> str:
    return Client().get(f"/reports/{query}").content.decode()


def test_page_shows_title_heading_subtitle_without_export_button(riverside: Branch) -> None:
    response = Client().get("/reports/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "<title>Monthly report · ReviewRadar</title>" in html
    assert "Monthly report</h1>" in html
    assert "Reviews and average score per location for one month (Vietnam time)." in html
    assert "Export JSON" not in html


def test_table_has_headers_and_one_row_per_location_sorted_by_name(riverside: Branch) -> None:
    html = _html()
    for header in ("Location", "Reviews", "Average", "Good (4–5)", "Bad (1–2)"):
        assert f">{header}</th>" in html
    assert html.index("Airport") < html.index("Riverside")
    assert f'href="/locations/{riverside.pk}/"' in html
    assert ">3.3<" in html
    assert ">—<" in html


def test_month_select_lists_12_months_with_current_selected(riverside: Branch) -> None:
    html = _html()
    assert 'for="report-month"' in html
    assert ">Month</label>" in html
    assert html.count("<option") == 12
    assert '<option value="2026-11" selected>November 2026</option>' in html


def test_chosen_month_is_selected_and_shown(riverside: Branch) -> None:
    html = _html("?month=2026-07")
    assert '<option value="2026-07" selected>July 2026</option>' in html
    assert ">1.0<" in html


@pytest.mark.parametrize("value", ["2026-13", "abc", "2024-01", ""])
def test_wrong_month_shows_current_month_without_error(riverside: Branch, value: str) -> None:
    html = _html(f"?month={value}")
    assert '<option value="2026-11" selected>' in html
    assert "alert" not in html


def test_form_reads_year_month() -> None:
    assert ReportMonthForm({"month": "2026-07"}).month() is not None
    assert ReportMonthForm({"month": "2026-13"}).month() is None
    assert ReportMonthForm({"month": "abc"}).month() is None
    assert ReportMonthForm({}).month() is None


def test_empty_month_lists_locations_and_a_line(riverside: Branch) -> None:
    html = _html("?month=2026-09")
    assert "Airport" in html
    assert "Riverside" in html
    assert "No reviews in September 2026." in html


def test_no_locations_shows_message_and_no_table(db: None) -> None:
    html = _html()
    assert "No locations yet" in html
    assert "<table" not in html


def test_sidebar_item_sits_between_reviews_and_reply_drafts(riverside: Branch) -> None:
    html = _html()
    assert html.index("Reviews\n        </a>") < html.index("Reports") < html.index("Reply drafts")
    assert 'class="nav-item is-active" href="/reports/" aria-current="page"' in html


def test_page_uses_one_query(
    riverside: Branch, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(2):
        Client().get("/reports/")


def test_table_scrolls_inside_wrapper(riverside: Branch) -> None:
    assert 'class="table-wrap"' in _html()


@pytest.mark.login
@pytest.mark.django_db
def test_visitor_not_signed_in_goes_to_login() -> None:
    response = Client().get("/reports/")
    assert response.status_code == 302
    assert response["Location"] == "/login/?next=/reports/"


@pytest.mark.login
@pytest.mark.django_db
def test_signed_in_user_sees_page() -> None:
    client = Client()
    client.force_login(get_user_model().objects.create_user(username="anna", password="x"))
    assert client.get("/reports/").status_code == 200

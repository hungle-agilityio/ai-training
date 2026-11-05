from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.models import Branch, Business, Review

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)
HEADER = "Location,Reviews,Average,Good,Bad,Change vs previous month"


@pytest.fixture(autouse=True)
def fixed_now(mocker: MockerFixture) -> None:
    mocker.patch("reviews.views.timezone.now", return_value=NOW)


def _branch(name: str) -> Branch:
    business = Business.objects.get_or_create(name="Demo")[0]
    return Branch.objects.create(business=business, name=name)


def _review(branch: Branch, year: int, month: int, rating: int) -> None:
    Review.objects.create(
        branch=branch,
        rating=rating,
        text="ok",
        created_at=datetime(year, month, 10, 5, 0, tzinfo=UTC),
    )


def _body(client: Client, query: str = "") -> str:
    return client.get(f"/reports/export/{query}").content.decode("utf-8")


@pytest.mark.django_db
def test_report_page_links_to_the_export_of_the_shown_month(client: Client) -> None:
    html = client.get("/reports/?month=2026-09").content.decode()

    assert 'href="/reports/export/?month=2026-09"' in html
    assert "Export CSV" in html


@pytest.mark.django_db
def test_export_has_same_rows_as_the_page_with_number_rules(client: Client) -> None:
    up, down, same, quiet = _branch("Up"), _branch("Down"), _branch("Same"), _branch("=Quiet")
    for branch, before, now in ((up, 3, 4), (down, 5, 4), (same, 4, 4)):
        _review(branch, 2026, 10, before)
        _review(branch, 2026, 11, now)
    _review(quiet, 2026, 11, 2)

    text = _body(client)

    assert text.startswith("﻿" + HEADER + "\r\n")
    assert text.split("\r\n")[1:5] == [
        "'=Quiet,1,2.0,0,1,",
        "Down,1,4.0,1,0,-1.0",
        "Same,1,4.0,1,0,0.0",
        "Up,1,4.0,1,0,+1.0",
    ]


@pytest.mark.django_db
def test_location_without_reviews_has_empty_average_and_change(client: Client) -> None:
    _branch("Quiet")

    assert _body(client).split("\r\n")[1] == "Quiet,0,,0,0,"


@pytest.mark.django_db
def test_download_name_follows_the_month_in_the_file(client: Client) -> None:
    response = client.get("/reports/export/?month=2026-09")

    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert response["Content-Disposition"] == (
        'attachment; filename="reviewradar-report-2026-09.csv"'
    )


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["", "?month=nonsense", "?month=2020-01"])
def test_wrong_month_gives_the_current_month_file(client: Client, query: str) -> None:
    response = client.get(f"/reports/export/{query}")

    assert "reviewradar-report-2026-11.csv" in response["Content-Disposition"]


@pytest.mark.django_db
def test_export_makes_at_most_two_queries(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    for name in ("A", "B", "C"):
        _review(_branch(name), 2026, 11, 4)

    with django_assert_max_num_queries(2):
        _body(client)


@pytest.mark.django_db
@pytest.mark.login
def test_visitor_is_sent_to_sign_in() -> None:
    response = Client().get("/reports/export/")

    assert response.status_code == 302
    assert response["Location"] == "/login/?next=/reports/export/"

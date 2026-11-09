import csv
import io

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch
from reviews.services import CSV_BOM

pytestmark = pytest.mark.django_db


@pytest.fixture
def demo() -> dict[str, int]:
    call_command("seed_demo_data")
    return {b.name: b.pk for b in Branch.objects.all()}


def _query(ids: dict[str, int], period: str = "") -> str:
    return f"a={ids['Downtown']}&b={ids['Riverside']}&period={period}"


def test_page_shows_download_button_only_with_a_valid_comparison(demo: dict[str, int]) -> None:
    client = Client()
    html = client.get(f"/compare/?{_query(demo, '30')}").content.decode()
    assert 'class="button"' in html
    assert "Download CSV" in html
    assert (
        f'href="/compare/export/?a={demo["Downtown"]}&amp;b={demo["Riverside"]}&amp;period=30"'
        in html
    )
    for query in ("", f"?a={demo['Downtown']}&b={demo['Downtown']}"):
        assert "Download CSV" not in client.get(f"/compare/{query}").content.decode()


def test_export_rows_bom_and_file_name(demo: dict[str, int]) -> None:
    response = Client().get(f"/compare/export/?{_query(demo)}")
    text = response.content.decode("utf-8")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert response["Content-Disposition"] == (
        'attachment; filename="compare-downtown-riverside-all-time.csv"'
    )
    assert text.startswith(CSV_BOM)
    rows = list(csv.reader(io.StringIO(text[len(CSV_BOM) :])))
    assert rows[0] == ["Measure", "Downtown", "Riverside"]
    assert [r[0] for r in rows[1:]] == [
        "Reviews",
        "Score",
        "Good reviews %",
        "Bad reviews %",
        "Replied in 24h %",
        "5 stars",
        "4 stars",
        "3 stars",
        "2 stars",
        "1 star",
    ]
    by_name = {r[0]: r for r in rows}
    assert by_name["Score"][1:] == ["4.0", "3.4"]
    assert by_name["Replied in 24h %"][1:] == ["", "100"]


def test_file_name_carries_the_period(demo: dict[str, int]) -> None:
    for period, slug in (("30", "30-days"), ("90", "90-days")):
        response = Client().get(f"/compare/export/?{_query(demo, period)}")
        assert f"compare-downtown-riverside-{slug}.csv" in response["Content-Disposition"]


def test_names_are_safe_for_a_spreadsheet(demo: dict[str, int]) -> None:
    Branch.objects.filter(pk=demo["Downtown"]).update(name="=Evil")
    text = Client().get(f"/compare/export/?{_query(demo)}").content.decode("utf-8")
    assert "'=Evil" in text.splitlines()[0]


@pytest.mark.parametrize("query", ["", "?a=1", "?a=1&b=1", "?a=1&b=99999&period=30"])
def test_export_without_a_valid_comparison_redirects_with_the_query(
    demo: dict[str, int], query: str
) -> None:
    response = Client().get(f"/compare/export/{query}")
    assert response.status_code == 302
    assert response["Location"] == f"/compare/{query}"


def test_export_makes_at_most_two_queries(
    demo: dict[str, int], django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(2):
        Client().get(f"/compare/export/?{_query(demo, '90')}")

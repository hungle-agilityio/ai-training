import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch

pytestmark = pytest.mark.django_db


@pytest.fixture
def demo() -> dict[str, int]:
    call_command("seed_demo_data")
    return {b.name: b.pk for b in Branch.objects.all()}


def _get(query: str = "") -> str:
    return Client().get(f"/compare/{query}").content.decode()


def _pair(ids: dict[str, int], period: str = "") -> str:
    return _get(f"?a={ids['Downtown']}&b={ids['Riverside']}&period={period}")


def test_page_title_heading_subtitle_without_export_button(demo: dict[str, int]) -> None:
    response = Client().get("/compare/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "<title>Compare locations · ReviewRadar</title>" in html
    assert "Compare locations</h1>" in html
    assert "Two locations side by side for a period." in html
    assert "Export JSON" not in html


def test_form_has_selects_period_options_and_button(demo: dict[str, int]) -> None:
    html = _get()
    assert 'id="compare-form"' in html
    assert 'method="get"' in html
    for text in ("Location A", "Location B", "Period", "Choose a location", "Compare"):
        assert text in html
    for name in ("Downtown", "Riverside"):
        assert name in html
    for label in ("All time", "Last 30 days", "Last 90 days"):
        assert label in html


def test_chosen_values_stay_selected(demo: dict[str, int]) -> None:
    html = _get(f"?a={demo['Downtown']}&b={demo['Riverside']}&period=30")
    assert f'<option value="{demo["Downtown"]}" selected>' in html
    assert f'<option value="{demo["Riverside"]}" selected>' in html
    assert '<option value="30" selected>' in html


def test_nothing_or_one_location_asks_for_two(demo: dict[str, int]) -> None:
    for query in ("", f"?a={demo['Downtown']}", f"?b={demo['Downtown']}"):
        html = _get(query)
        assert "Pick two locations to compare." in html
        assert "compare-table" not in html


def test_unknown_id_or_period_never_errors(demo: dict[str, int]) -> None:
    response = Client().get("/compare/?a=99999&b=abc&period=7")
    assert response.status_code == 200
    assert "Pick two locations to compare." in response.content.decode()
    html = _get(f"?a={demo['Downtown']}&b={demo['Riverside']}&period=7")
    assert "compare-table" in html
    assert '<option value="" selected>All time' in html


def test_same_location_twice_shows_message(demo: dict[str, int]) -> None:
    pk = demo["Downtown"]
    html = _get(f"?a={pk}&b={pk}")
    assert "Choose two different locations." in html
    assert "compare-table" not in html
    assert "Pick two locations to compare." not in html


def test_demo_all_time_numbers(demo: dict[str, int]) -> None:
    html = _pair(demo)
    assert 'id="compare-table"' in html
    assert "Downtown scores 0.6 higher than Riverside" in html
    for text in ("4.0", "3.4", "Good reviews", "Bad reviews", "Replied in 24h", "60%", "40%", "—"):
        assert text in html
    assert "5 ★" in html
    assert "1 ★" in html


def test_demo_last_30_days_same_score(demo: dict[str, int]) -> None:
    html = _pair(demo, "30")
    assert "Same score" in html
    assert html.count("4.5") >= 2


def test_lower_sentence_has_no_minus_sign(demo: dict[str, int]) -> None:
    html = _get(f"?a={demo['Riverside']}&b={demo['Downtown']}")
    assert "Riverside scores 0.6 lower than Downtown" in html
    assert "-0.6" not in html


def test_two_queries_for_any_number_of_reviews(
    demo: dict[str, int], django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(2):
        Client().get(f"/compare/?a={demo['Downtown']}&b={demo['Riverside']}")


def test_stylesheet_has_compare_rules() -> None:
    from pathlib import Path

    css = (Path(__file__).parents[2] / "static/reviews/app.css").read_text()
    assert ".compare-table" in css

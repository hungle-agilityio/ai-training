import re

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business

pytestmark = pytest.mark.django_db


@pytest.fixture
def demo() -> dict[str, int]:
    call_command("seed_demo_data")
    return {b.name: b.pk for b in Branch.objects.all()}


def _panel(demo: dict[str, int], period: str = "") -> str:
    url = f"/compare/?a={demo['Downtown']}&b={demo['Riverside']}&period={period}"
    html = Client().get(url).content.decode()
    match = re.search(r'<section[^>]*id="compare-topics".*?</section>', html, re.S)
    assert match, "panel #compare-topics missing"
    return match.group(0)


def _rows(panel: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for row in re.findall(r"<tr>(.*?)</tr>", panel, re.S):
        label = re.search(r"<th[^>]*>(.*?)</th>", row, re.S)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if label and len(cells) == 2:
            rows[re.sub(r"\s+", " ", label.group(1)).strip()] = (
                re.sub(r"\s+", " ", cells[0]).strip(),
                re.sub(r"\s+", " ", cells[1]).strip(),
            )
    return rows


def test_panel_title_and_all_time_numbers(demo: dict[str, int]) -> None:
    panel = _panel(demo)
    assert "What customers talk about" in panel
    assert _rows(panel) == {
        "Wait time": ("1", "0"),
        "Staff": ("2", "1 · 1 bad"),
        "Doctor &amp; treatment": ("1", "2"),
        "Price &amp; billing": ("1", "0"),
        "Booking &amp; phone": ("0", "1 · 1 bad"),
        "Parking": ("1", "1"),
        "Cleanliness": ("1", "0"),
    }


def test_panel_last_30_days_leaves_out_empty_topics(demo: dict[str, int]) -> None:
    rows = _rows(_panel(demo, "30"))
    assert rows == {
        "Staff": ("1", "0"),
        "Doctor &amp; treatment": ("0", "1"),
        "Parking": ("0", "1"),
        "Cleanliness": ("1", "0"),
    }


def test_panel_follows_topic_order(demo: dict[str, int]) -> None:
    labels = list(_rows(_panel(demo)))
    assert labels[0] == "Wait time"
    assert labels[-1] == "Cleanliness"


def test_empty_message_when_no_topic_has_a_review() -> None:
    business = Business.objects.create(name="B")
    a = Branch.objects.create(name="Alpha", business=business)
    b = Branch.objects.create(name="Beta", business=business)
    html = Client().get(f"/compare/?a={a.pk}&b={b.pk}").content.decode()
    assert "No topics found for these locations in this period." in html


def test_no_panel_without_two_locations(demo: dict[str, int]) -> None:
    html = Client().get("/compare/").content.decode()
    assert 'id="compare-topics"' not in html


def test_at_most_four_queries(
    demo: dict[str, int], django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(4):
        Client().get(f"/compare/?a={demo['Downtown']}&b={demo['Riverside']}")

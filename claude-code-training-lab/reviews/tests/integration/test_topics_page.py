import re

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business
from reviews.repositories import create_review

pytestmark = pytest.mark.django_db


def _get(query: str = "") -> str:
    return Client().get(f"/topics/{query}").content.decode()


@pytest.fixture
def demo() -> None:
    call_command("seed_demo_data")


def test_page_title_heading_subtitle_without_export_button(demo: None) -> None:
    response = Client().get("/topics/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "<title>Topics · ReviewRadar</title>" in html
    assert "Topics</h1>" in html
    assert "What customers talk about, by topic." in html
    assert "Export JSON" not in html


def test_sidebar_link_sits_between_reports_and_reply_drafts_and_is_active(demo: None) -> None:
    html = _get()
    assert html.index("Reports\n") < html.index("Topics\n        </a>") < html.index("Reply drafts")
    link = re.search(r'<a class="nav-item is-active" href="/topics/" aria-current="page">', html)
    assert link is not None
    assert 'href="/reports/" aria-current' not in html


def test_sidebar_link_is_not_active_on_other_pages(demo: None) -> None:
    html = Client().get("/reports/").content.decode()
    assert 'href="/topics/"' in html
    assert 'class="nav-item is-active" href="/topics/"' not in html


def test_filters_form_has_location_and_period_options(demo: None) -> None:
    html = _get()
    assert 'id="topics-location" name="location"' in html
    assert 'id="topics-period" name="period"' in html
    for label in ("All locations", "Airport", "All time", "Last 30 days", "Last 90 days", "Apply"):
        assert label in html
    assert '<option value="30">Last 30 days</option>' in html
    assert '<option value="" selected>All time</option>' in html


def test_chosen_values_are_selected(demo: None) -> None:
    airport = Branch.objects.get(name="Airport")
    html = _get(f"?location={airport.pk}&period=90")
    assert f'<option value="{airport.pk}" selected>Airport</option>' in html
    assert '<option value="90" selected>Last 90 days</option>' in html


def test_wrong_values_are_ignored_and_the_other_still_applies(demo: None) -> None:
    airport = Branch.objects.get(name="Airport")
    html = _get("?location=abc&period=30")
    assert '<option value="30" selected>Last 30 days</option>' in html
    assert '<option value="" selected>All locations</option>' in html
    html = _get(f"?location={airport.pk}&period=7")
    assert f'<option value="{airport.pk}" selected>Airport</option>' in html
    assert '<option value="" selected>All time</option>' in html
    assert '<option value="" selected>All locations</option>' in _get("?location=999999")


def test_summary_line_of_the_demo(demo: None) -> None:
    assert '<p id="topics-summary">14 reviews · 1 mentions no topic</p>' in _get()


def test_summary_line_plural_and_singular(db: None) -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="B"), name="A")
    create_review(branch=branch, rating=5, text="zzz", created_at=timezone.now())
    assert ">1 review · 1 mentions no topic<" in _get()
    create_review(branch=branch, rating=5, text="qqq", created_at=timezone.now())
    assert ">2 reviews · 2 mention no topic<" in _get()
    create_review(branch=branch, rating=5, text="the wait was long", created_at=timezone.now())
    assert ">3 reviews · 2 mention no topic<" in _get()


def test_table_lists_all_seven_topics_most_reviews_first(demo: None) -> None:
    html = _get()
    table = html[html.index('id="topics-table"') : html.index("</table>")]
    assert html.index('class="table-wrap"') < html.index('id="topics-table"')
    for header in ("Topic", "Reviews", "Share", "Bad", "Average rating"):
        assert f'<th scope="col">{header}</th>' in table
    rows = re.findall(r'<tr>\s*<th scope="row">([^<]+)</th>\s*<td>(\d+)</td>', table)
    assert len(rows) == 7
    counts = [int(count) for _, count in rows]
    assert counts == sorted(counts, reverse=True)
    labels_of_four = [label for label, count in rows if count == "4"]
    assert labels_of_four == sorted(labels_of_four)
    assert "<td>50%</td>" not in table
    assert "2 (50%)" in table
    assert "<td>29%</td>" in table
    assert "<td>4.0</td>" in table


def test_topic_without_reviews_shows_zero_row_without_link(db: None) -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="B"), name="A")
    create_review(branch=branch, rating=2, text="long wait", created_at=timezone.now())
    html = _get()
    row = re.search(r"<th scope=\"row\">Staff</th>(.*?)</tr>", html, re.S)
    assert row is not None
    cells = re.findall(r"<td>(.*?)</td>", row.group(1), re.S)
    assert cells == ["0", "0%", "0", "–", ""]
    wait = re.search(r"<th scope=\"row\">Wait time</th>(.*?)</tr>", html, re.S)
    assert wait is not None
    assert "1 (100%)" in wait.group(1)
    assert "2.0" in wait.group(1)


def test_see_reviews_link_with_and_without_location(demo: None) -> None:
    assert 'href="/reviews/?topic=wait"' in _get()
    airport = Branch.objects.get(name="Airport")
    html = _get(f"?location={airport.pk}&period=30")
    assert f'href="/reviews/?topic=wait&amp;location={airport.pk}"' in html
    assert "period=" not in html.split('id="topics-table"')[1]


def test_airport_shows_four_reviews_with_wait_first(demo: None) -> None:
    airport = Branch.objects.get(name="Airport")
    html = _get(f"?location={airport.pk}")
    assert ">4 reviews" in html
    table = html[html.index('id="topics-table"') :]
    assert table.index("Wait time") < table.index("Staff")


def test_no_reviews_at_all_shows_empty_block(db: None) -> None:
    html = _get()
    assert "No reviews yet" in html
    assert "Topics will appear here as soon as there are reviews." in html
    assert 'id="topics-summary"' not in html
    assert 'id="topics-table"' not in html


def test_selection_without_reviews_keeps_the_table_with_zeros(db: None) -> None:
    business = Business.objects.create(name="B")
    full = Branch.objects.create(business=business, name="Full")
    empty = Branch.objects.create(business=business, name="Empty")
    create_review(branch=full, rating=4, text="great staff", created_at=timezone.now())
    html = _get(f"?location={empty.pk}")
    assert '<p id="topics-summary">0 reviews</p>' in html
    assert "No reviews yet" not in html
    table = html[html.index('id="topics-table"') :]
    assert table.count("<td>–</td>") == 7
    assert "See reviews" not in table


def test_query_count_is_at_most_two_with_many_locations_and_reviews(
    db: None, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="B")
    branches = Branch.objects.bulk_create(
        [Branch(business=business, name=f"L{i:03d}") for i in range(200)]
    )
    now = timezone.now()
    for i in range(500):
        create_review(branch=branches[i % 200], rating=i % 5 + 1, text="long wait", created_at=now)
    client = Client()
    with django_assert_max_num_queries(2):
        response = client.get("/topics/?period=30")
    assert response.status_code == 200

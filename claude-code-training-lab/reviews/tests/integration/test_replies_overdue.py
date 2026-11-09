from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.forms import OverdueForm
from reviews.models import Branch, Business, Review, ReviewReply

TITLE = 'title="No reply for more than 24 hours"'


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


def add(branch: Branch, rating: int, hours_ago: int, text: str) -> Review:
    return Review.objects.create(
        branch=branch,
        rating=rating,
        text=text,
        created_at=timezone.now() - timedelta(hours=hours_ago),
    )


def tabs(page: str) -> str:
    return page.split('class="reply-tabs"')[1].split("</nav>")[0]


def html(query: str = "") -> str:
    response = Client().get("/replies/" + query)
    assert response.status_code == 200
    return response.content.decode()


def test_all_view_marks_all_tab_current(branch: Branch) -> None:
    add(branch, 1, 30, "Old bad")
    page = html()
    assert 'href="/replies/" aria-current="page"' in tabs(page)
    assert 'href="/replies/?overdue=1"' in tabs(page)
    assert tabs(page).count('aria-current="page"') == 1


def test_overdue_view_marks_overdue_tab_current(branch: Branch) -> None:
    add(branch, 1, 30, "Old bad")
    page = html("?overdue=1")
    assert 'href="/replies/?overdue=1" aria-current="page"' in tabs(page)
    assert tabs(page).count('aria-current="page"') == 1


def test_tabs_carry_no_number(branch: Branch) -> None:
    add(branch, 1, 30, "Old bad")
    block = tabs(html())
    assert ">Overdue only</a>" in block
    assert ">All</a>" in block
    assert "<span" not in block


@pytest.mark.parametrize("value", ["0", "abc", "", "2"])
def test_other_values_show_all_view(branch: Branch, value: str) -> None:
    add(branch, 1, 30, "Old bad")
    add(branch, 2, 1, "New bad")
    page = html(f"?overdue={value}")
    assert "2 reviews need a reply" in page
    assert "New bad" in page


def test_missing_value_shows_all_view(branch: Branch) -> None:
    add(branch, 2, 1, "New bad")
    assert "New bad" in html()


def test_overdue_form_reads_only_one() -> None:
    assert OverdueForm({"overdue": "1"}).is_overdue() is True
    assert OverdueForm({"overdue": "0"}).is_overdue() is False
    assert OverdueForm({}).is_overdue() is False


def test_label_only_on_overdue_rows_in_both_tabs(branch: Branch) -> None:
    add(branch, 1, 30, "Old bad")
    add(branch, 2, 1, "New bad")
    assert html().count(TITLE) == 1
    assert html("?overdue=1").count(TITLE) == 1
    assert "New bad" not in html("?overdue=1")


def test_overdue_count_line_singular_and_plural(branch: Branch) -> None:
    add(branch, 1, 30, "One")
    assert "1 overdue review needs a reply" in html("?overdue=1")
    add(branch, 2, 40, "Two")
    page = html("?overdue=1")
    assert "2 overdue reviews need a reply" in page
    assert "Showing 1-2 of 2 reviews" in page


def test_overdue_page_two_keeps_filter(branch: Branch) -> None:
    for i in range(21):
        add(branch, 1, 30 + i, f"Bad {i}")
    page = html("?overdue=1&page=2")
    assert "Showing 21-21 of 21 reviews" in page
    pager = page.split('class="pager"')[1]
    assert "overdue=1&amp;page=1" in pager


def test_empty_overdue_view(branch: Branch) -> None:
    add(branch, 2, 1, "New bad")
    page = html("?overdue=1")
    assert "<h2>No overdue reviews</h2>" in page
    assert "Every bad review older than 24 hours has a reply." in page
    assert '<a href="/replies/">Show all reviews</a>' in page
    assert "<table" not in page
    assert "All caught up" not in page


def test_empty_all_view_keeps_all_caught_up(branch: Branch) -> None:
    page = html()
    assert "All caught up" in page
    assert "No overdue reviews" not in page


def test_replied_review_is_not_overdue(branch: Branch) -> None:
    review = add(branch, 1, 30, "Answered")
    now = timezone.now()
    ReviewReply.objects.create(review=review, text="Sorry", created_at=now, updated_at=now)
    assert "No overdue reviews" in html("?overdue=1")


@pytest.mark.django_db
def test_seed_demo_data_has_one_overdue_review() -> None:
    call_command("seed_demo_data", stdout=StringIO())
    overdue = html("?overdue=1")
    assert "1 overdue review needs a reply" in overdue
    assert "Billing mistake and nobody called back." in overdue
    assert overdue.count(TITLE) == 1
    everything = html()
    assert everything.count(TITLE) == 1
    assert "Waited 50 minutes, nobody apologized." in everything
    assert "Waited 50 minutes, nobody apologized." not in overdue


@pytest.mark.parametrize("query", ["", "?overdue=1"])
def test_query_count_is_constant(
    branch: Branch, query: str, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    for i in range(30):
        add(branch, 1, 30 + i, f"Bad {i}")
    with django_assert_max_num_queries(2):
        assert Client().get("/replies/" + query).status_code == 200

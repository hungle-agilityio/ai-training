from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review, ReviewReply

NOW = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


def add(branch: Branch, rating: int, days_ago: int, text: str = "Text") -> Review:
    return Review.objects.create(
        branch=branch, rating=rating, text=text, created_at=NOW - timedelta(days=days_ago)
    )


def reply_to(review: Review) -> None:
    ReviewReply.objects.create(review=review, text="Thanks", created_at=NOW, updated_at=NOW)


def html(query: str = "") -> str:
    response = Client().get("/replies/" + query)
    assert response.status_code == 200
    return response.content.decode()


def test_page_has_title_heading_subtitle_and_no_export_button(branch: Branch) -> None:
    page = html()
    assert "<title>Reply drafts · ReviewRadar</title>" in page
    assert "<h1>Reply drafts</h1>" in page
    assert "Reviews that still need a reply, worst first." in page
    assert "Export JSON" not in page


def test_sidebar_item_is_an_active_link_without_soon(branch: Branch) -> None:
    page = html()
    assert 'class="nav-item is-active" href="/replies/" aria-current="page"' in page
    assert page.index("Reports") < page.index('href="/replies/"')
    assert "Reply drafts <em>Soon</em>" not in page
    assert page.count("is-disabled") == 1  # Settings only


def test_sidebar_item_is_not_active_on_other_pages(branch: Branch) -> None:
    page = Client().get("/reviews/").content.decode()
    assert 'class="nav-item" href="/replies/"' in page


def test_only_reviews_without_reply_are_listed(branch: Branch) -> None:
    add(branch, 1, 1, "needs one")
    reply_to(add(branch, 1, 2, "has one"))
    page = html()
    assert 'id="reply-queue"' in page
    assert "needs one" in page
    assert "has one" not in page
    assert "1 review needs a reply" in page


def test_count_line_is_plural_for_several(branch: Branch) -> None:
    add(branch, 2, 1)
    add(branch, 2, 2)
    assert "2 reviews need a reply" in html()


def test_order_is_bad_then_three_then_good_oldest_first_then_lowest_id(branch: Branch) -> None:
    add(branch, 5, 9, "good-old")
    add(branch, 3, 1, "three")
    add(branch, 1, 1, "bad-new")
    add(branch, 2, 5, "bad-old")
    add(branch, 4, 2, "good-new")
    add(branch, 1, 3, "tie-a")
    add(branch, 1, 3, "tie-b")
    page = html()
    order = ["bad-old", "tie-a", "tie-b", "bad-new", "three", "good-old", "good-new"]
    positions = [page.index(name) for name in order]
    assert positions == sorted(positions)


def test_table_headers_and_row_format(branch: Branch) -> None:
    add(branch, 2, 1, "x" * 150)
    page = html()
    for header in ("Location", "Rating", "Review text", "Date"):
        assert '<th scope="col">' + header + "</th>" in page
    assert "Sentiment" not in page
    assert 'href="/locations/' + str(branch.id) + '/"' in page
    assert 'aria-label="2 out of 5"' in page
    assert 'data-sensitive="review-text"' in page
    assert "x" * 120 + "…" in page
    assert "<time" in page


def test_twenty_per_page_with_pager(branch: Branch) -> None:
    for day in range(25):
        add(branch, 4, day + 1)
    page = html()
    assert "Showing 1-20 of 25 reviews" in page
    assert page.count('class="review-row"') == 20
    assert 'rel="next"' in page
    assert "Showing 21-25 of 25 reviews" in html("?page=2")


@pytest.mark.parametrize("query", ["?page=abc", "?page=0", "?page=-3"])
def test_wrong_page_shows_first_page(branch: Branch, query: str) -> None:
    for day in range(25):
        add(branch, 4, day + 1)
    assert "Showing 1-20 of 25 reviews" in html(query)


def test_too_high_page_shows_last_page(branch: Branch) -> None:
    for day in range(25):
        add(branch, 4, day + 1)
    assert "Showing 21-25 of 25 reviews" in html("?page=99")


def test_empty_when_no_reviews(branch: Branch) -> None:
    page = html()
    assert "All caught up" in page
    assert "Every review has a reply." in page
    assert "<table" not in page


def test_empty_when_every_review_has_a_reply(branch: Branch) -> None:
    reply_to(add(branch, 1, 1))
    page = html()
    assert "All caught up" in page
    assert "<table" not in page


def test_table_scrolls_inside_wrapper(branch: Branch) -> None:
    add(branch, 1, 1)
    assert 'class="table-wrap"' in html()


@pytest.mark.parametrize("count", [5, 50])
def test_page_makes_at_most_two_queries(
    branch: Branch, count: int, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    for day in range(count):
        add(branch, 1 + day % 5, day + 1)
    with django_assert_max_num_queries(2):
        Client().get("/replies/")


def test_styles_come_from_replies_css_after_app_css(branch: Branch) -> None:
    page = html()
    assert page.index("reviews/app.css") < page.index("reviews/replies.css")


@pytest.mark.login
@pytest.mark.django_db
def test_visitor_not_signed_in_goes_to_login() -> None:
    response = Client().get("/replies/")
    assert response.status_code == 302
    assert response["Location"] == "/login/?next=/replies/"


@pytest.mark.login
@pytest.mark.django_db
def test_signed_in_user_sees_page() -> None:
    client = Client()
    client.force_login(get_user_model().objects.create_user(username="anna", password="x"))
    assert client.get("/replies/").status_code == 200
